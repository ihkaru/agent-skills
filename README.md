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

### 3. arc42 Architecture & Drift Tracking Skill (`arc42-architect`)
- Guides modular architecture documentation following the international **arc42** standard (ISO/IEC/IEEE 42010 aligned).
- Enforces **Numbered Modular Files** (`01_` to `12_` in `docs/architecture/`) preventing oversized markdown files.
- **Git Provenance & Freshness**: Embeds baseline commit SHA and timestamp per section to track documentation staleness.
- **Architecture Drift Detection**: Deterministic audit via `arc42-lint` to detect when source code has evolved past documentation.
- Supports native **Mermaid C4** diagrams (`C4Context`, `C4Container`, `C4Component`, sequence flows) and **Q42 Quality Model** (492 tags across 8 properties).
- Tailored for both greenfield systems and **in-flight / half-baked project reverse engineering**.

### 4. Google OSV-Scanner Dependency Security Gate (`osv-scanner`)
- High-performance, language-agnostic dependency vulnerability scanner and remediation gate (Google OSV-Scanner).
- Covers polyglot ecosystems: PHP (`composer.lock`), Node/TS (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lock`), Python (`poetry.lock`, `uv.lock`, `Pipfile.lock`, `requirements.txt`), Go (`go.mod`), Rust (`Cargo.lock`), Java (`pom.xml`, `gradle.lockfile`), and container SBOMs.
- Features **zero-overhead git staged mode** (`osv-scanner-gate --staged`) executing in <0.05s when no manifests changed.
- Automated guided remediation (`osv-scanner fix`) computing non-breaking upgrade paths.
- Declarative audit trail and time-boxed debt exemptions via `osv-scanner.toml`.

### 5. Zero-Mock & Static Invariant Detector (`zero-mock-detector`)
- High-precision AST static analyzer detecting mock leakage, silent dummies, bodyless stubs, and fake latency in production pathways.
- Enforces Dual-Tier Verification and repository-level technical debt citations.

### 6. Deterministic Built-in CLI Tools (Installed to `~/.local/bin/`)
- **`osv-scanner-gate` / `osv-gate`**: Fast polyglot dependency CVE scanner and git pre-commit security gate (`--staged`, `--json`, `--fix`, `--min-severity`).
- **`arc42-lint`**: arc42 cross-section consistency, git provenance, and architecture drift linter (`--json`, `--check-drift`, `--strict`).
- **`arc42-pre-commit`**: Automated Git pre-commit gate blocking stale documentation and unstaged architecture changes (`arc42-lint --install-hook`).
- **`detect-mocks` / `zero-mock-detector`**: Production mock leakage and bodyless stub static detector.
- **`coolify-control`**: Agnostic container discovery, live log inspection, deployment logs, and database query CLI.
- **`codegraph-impact`**: AST & CodeGraph blast radius analyzer (callers, callees, affected test suites).
- **`static-srp-analyzer`**: Deterministic static analyzer detecting bloated components (>180 lines, >50 lines functions) and abstraction bypasses.
- **`vsa-boundary-checker`**: Architectural boundary linter forbidding cross-slice direct imports.

### 7. Global & Repo-Level Guidelines
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
3. Auto-bootstrap `osv-scanner` binary if not present.
4. Expose global executable commands (`osv-scanner-gate`, `coolify-control`, `static-srp-analyzer`, `codegraph-impact`, `vsa-boundary-checker`, `arc42-lint`, `detect-mocks`) into `~/.local/bin/`.
5. Run verification tests across all toolchains.

---

## 🧪 Verification

All tools include isolated, hermetic, zero-network unit tests:

```bash
python3 ~/.agent-skills/skills/craftsman-coder/scripts/test_codegraph_impact.py
python3 ~/.agent-skills/skills/craftsman-coder/scripts/test_static_srp_analyzer.py
python3 ~/.agent-skills/skills/craftsman-coder/scripts/test_vsa_boundary_checker.py
python3 ~/.agent-skills/skills/thinkstation-coolify/scripts/test_coolify_control.py
python3 ~/.agent-skills/skills/zero-mock-detector/tests/test_detector.py
python3 ~/.agent-skills/skills/arc42-architect/tests/test_arc42_lint.py
python3 ~/.agent-skills/skills/osv-scanner/tests/test_osv_scanner_gate.py
```

---

## 📄 License

[MIT](LICENSE) © 2026 Ihza Karunia (ihkaru)
