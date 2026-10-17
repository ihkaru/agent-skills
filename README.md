# ⚡ Agent Skills & Craftsman Coder Toolchain

A disciplined, repo-agnostic engineering configuration, skills, and deterministic toolchain for **Antigravity CLI (AGY)** and modern AI coding agents.

---

## 🌟 What's Included

### 1. Craftsman Coder Skill (`craftsman-coder`)
- Enforces **SOLID** and strict **Single Responsibility Principle (SRP)**.
- Mandates **Dependency Injection (DI)** for high cohesion and testability.
- Architectural fallback to **Vertical Slice Architecture (VSA)** + **Enterprise Integration Patterns (EIP)**.
- Optimal **Big-O** complexity selection backed by real-time web research.
- High-performance, low-RAM libraries with enterprise-safe permissive licenses (**MIT / Apache-2.0 / BSD**).
- Anchored in the **"Old Coder"** philosophy: *"Review evidence, not code."*

### 2. ThinkStation Coolify & Database Skill (`thinkstation-coolify`)
- Automated SSH management and operational control for the ThinkStation Coolify server (`*.dvlpid.my.id`).
- Resilient connection over **Tailscale Mesh VPN** (`100.101.49.42`) and LAN (`192.168.0.136`).
- Automatic SSH key provisioning from **Infisical Universal Auth**.
- Container-agnostic application discovery, live log inspection, and deployment queue tracking.
- Automated database engine classification (**PostgreSQL, MySQL, MariaDB, Redis**) with auto-credential query execution.

### 3. Deterministic Built-in CLI Tools (Installed to `~/.local/bin/`)
- **`coolify-control`**: Agnostic container discovery, live log inspection, deployment logs, and database query CLI.
- **`codegraph-impact`**: AST & CodeGraph blast radius analyzer (callers, callees, affected test suites).
- **`static-srp-analyzer`**: Deterministic static analyzer detecting bloated components (>180 lines, >50 lines functions) and abstraction bypasses.
- **`vsa-boundary-checker`**: Architectural boundary linter forbidding cross-slice direct imports.

### 4. Global & Repo-Level Guidelines
- `GEMINI.md` / `AGENTS.md` universal standing rules.
- Portable, git-ready repository-level `GEMINI.md` generation rules (zero external paths, zero hardcoded secrets).

---

## 🚀 Quick Install (Bootstrap Any Machine)

Clone and run the bootstrap script:

```bash
git clone https://github.com/ihkaru/agent-skills.git ~/.agent-skills
~/.agent-skills/install.sh
```

Or via one-liner:
```bash
curl -fsSL https://raw.githubusercontent.com/ihkaru/agent-skills/main/install.sh | bash
```

The installer will:
1. Register `~/.gemini/config/skills.json` and deploy global `GEMINI.md` rules.
2. Link all skills into `~/.gemini/config/skills/`.
3. Expose global executable commands (`coolify-control`, `static-srp-analyzer`, `codegraph-impact`, `vsa-boundary-checker`) into `~/.local/bin/`.
4. Run verification tests across all toolchains.

---

## 🧪 Verification

All tools include isolated, hermetic, zero-network unit tests:

```bash
python3 ~/.agent-skills/skills/craftsman-coder/scripts/test_codegraph_impact.py
python3 ~/.agent-skills/skills/craftsman-coder/scripts/test_static_srp_analyzer.py
python3 ~/.agent-skills/skills/craftsman-coder/scripts/test_vsa_boundary_checker.py
python3 ~/.agent-skills/skills/thinkstation-coolify/scripts/test_coolify_control.py
```

---

## 📄 License

[MIT](LICENSE) © 2026 Ihza Karunia (ihkaru)
