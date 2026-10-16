# ⚡ Agent Skills & Craftsman Coder Toolchain

A disciplined, repo-agnostic engineering configuration, skills, and deterministic toolchain for **Antigravity CLI (AGY)** and modern AI coding agents.

---

## 🌟 What's Included

1. **Craftsman Coder Skill (`craftsman-coder`)**:
   - Enforces **SOLID** and strict **Single Responsibility Principle (SRP)**.
   - Mandates **Dependency Injection (DI)** for high cohesion and testability.
   - Architectural fallback to **Vertical Slice Architecture (VSA)** + **Enterprise Integration Patterns (EIP)**.
   - Optimal **Big-O** complexity selection backed by real-time web research.
   - High-performance, low-RAM libraries with enterprise-safe permissive licenses (**MIT / Apache-2.0 / BSD**).
   - Anchored in the **"Old Coder"** philosophy: *"Review evidence, not code."*

2. **Deterministic Built-in Tools (MIT, Zero-Dependency Python 3)**:
   - `codegraph_impact.py`: AST & CodeGraph blast radius analyzer (callers, callees, affected test suites).
   - `static_srp_analyzer.py`: Deterministic static analyzer detecting bloated components (>180 lines) and abstraction bypasses.
   - `vsa_boundary_checker.py`: Architectural boundary linter forbidding cross-slice direct imports.

3. **Global & Repo-Level Guidelines**:
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

---

## 🧪 Verification

All tools include isolated, hermetic, parallel-ready unit tests:

```bash
python3 ~/.agent-skills/skills/craftsman-coder/scripts/test_codegraph_impact.py
python3 ~/.agent-skills/skills/craftsman-coder/scripts/test_static_srp_analyzer.py
python3 ~/.agent-skills/skills/craftsman-coder/scripts/test_vsa_boundary_checker.py
```

---

## 📄 License

[MIT](LICENSE) © 2026 Ihza Karunia (ihkaru)
