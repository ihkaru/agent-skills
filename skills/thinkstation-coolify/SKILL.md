---
name: thinkstation-coolify
description: >-
  Automated SSH management and operational control for the ThinkStation Coolify server hosting *.dvlpid.my.id.
  Enables container discovery, live log inspection, deployment queue monitoring, automated database discovery,
  and credential-injected SQL/Redis query execution across all applications in a container-agnostic manner.
---

# ThinkStation Coolify & Database Control Skill

A unified, container-agnostic skill and CLI tool for managing applications, monitoring live logs, tracking deployments, and querying databases on the Lenovo ThinkStation P320 server (`*.dvlpid.my.id`) via SSH.

---

## 1. Architectural Overview & Credentials

* **Server:** Lenovo ThinkStation P320 (`server-ThinkStation-P320`)
* **Operating System:** Ubuntu Linux (Kernel 7.0 / 6.8 x86_64)
* **Management Engine:** Coolify v4.1.2 + Traefik v3.6 (`coolify-proxy`)
* **Domain Wildcard:** `*.dvlpid.my.id`
* **Network & Routing:**
  * **Tailscale VPN IP:** `100.101.49.42` (Primary, encrypted WireGuard mesh)
  * **LAN IP:** `192.168.0.136` (Fallback local subnet)
  * **Port:** `22`
  * **User:** `server`
* **Infisical Secret Vault:**
  * Project ID: `f13379e0-9661-4f8e-81ef-0e81d1502da1` (`dev` environment)
  * Key: `SERVER_SSH_PRIVATE_KEY` -> automatically written to `~/.ssh/id_ed25519_agent`

---

## 2. CLI Tool: `coolify_control.py`

The core executable is located at:
`~/.gemini/config/skills/thinkstation-coolify/scripts/coolify_control.py`
*(Symlinked globally to `coolify-control`)*

### Design Principles (AI-Agent Ready):
1. **Machine-Readability First:** Every subcommand supports `--json` for structured, parseable JSON payloads.
2. **Zero Interactivity:** Batch mode SSH, no prompts, no manual password typing.
3. **Resilient Key Recovery:** If `~/.ssh/id_ed25519_agent` is missing or corrupted, the tool automatically fetches it from Infisical and sets `0600` permissions.
4. **Container Agnostic:** Works across all projects (Forex, Lumis AI, AksaraCAT, GardaData, DokterV, n8n, Windmill, etc.).

---

## 3. Workflow & Usage Patterns

### A. Health & Status Check
Check host connectivity, kernel, uptime, and Docker version:
```bash
python3 ~/.gemini/config/skills/thinkstation-coolify/scripts/coolify_control.py status [--json]
```

### B. Discovering Applications & Containers
List all running containers, along with Coolify project, resource name, domain, and status:
```bash
# List all running containers
coolify-control apps list

# Search by domain, application, or project
coolify-control apps list --search forex
coolify-control apps list --search dvlpid.my.id
coolify-control apps list --search lumis

# Output machine-readable JSON
coolify-control apps list --json
```

### C. Inspecting Container Details (Environment & Mounts)
Inspect environment variables, volumes, and open ports:
```bash
coolify-control apps inspect <container-name-or-id> [--json]
# Example:
coolify-control apps inspect api-server-fmm1i1dj48cq6aq3c3fhiexe-002828326984
```

### D. Viewing & Tailing Container Logs
Retrieve real-time application logs without needing manual SSH commands:
```bash
coolify-control logs <container-name-or-id> [--tail 100] [--timestamps]
# Example:
coolify-control logs ui-fmm1i1dj48cq6aq3c3fhiexe-002828350614 --tail 50
```

### E. Auditing Deployments & Build Logs
Monitor Coolify build pipelines and deployment history directly from `coolify-db`:
```bash
# List recent deployments across all projects
coolify-control deploy list [--limit 10]

# Filter by application name
coolify-control deploy list --app lumis

# View detailed deployment / build log (including failures & docker errors)
coolify-control deploy logs <deployment-id-or-app> [--tail 200]
# Example:
coolify-control deploy logs 1785 --tail 50

# Restart a service or container
coolify-control deploy restart <container-name-or-id>
```

### F. Automated Database Discovery & Querying
Discovers any database on ThinkStation (Postgres, Timescale, MySQL, MariaDB, Redis) and automatically executes queries using environment credentials:

```bash
# 1. List all active database containers and engines
coolify-control db list [--json]

# 2. Find which database container belongs to a project/app
coolify-control db find forex
coolify-control db find garda-data
coolify-control db find fintr

# 3. Query PostgreSQL / TimescaleDB
coolify-control db query jm4yiyys3rkhog64ld2psg6p --sql "SELECT current_database(), current_user;"
coolify-control db query voh5l4nf3trzgs5s0p2ohggy --sql "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"

# 4. Query MySQL / MariaDB (Credentials automatically extracted from container env)
coolify-control db query h139vp1fyu5dz7sgnq6wg984 --sql "SHOW TABLES;"
coolify-control db query ffhz4t4ki2gkwq5ryl10xf5b --sql "SELECT version();"

# 5. Query Redis / Valkey
coolify-control db query coolify-redis --sql "PING"
coolify-control db query coolify-redis --sql "INFO server"
```

### G. Raw Command Execution
Execute arbitrary commands on the ThinkStation server:
```bash
coolify-control exec "docker df && free -h"
```
