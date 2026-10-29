# Global Coding Guidelines & Architectural Principles

## 1. SOLID & Single Responsibility Principle (SRP)
- Prioritize SOLID principles in all code generation and refactoring.
- Enforce the **Single Responsibility Principle (SRP)**: Each class, module, and function must have only one reason to change. Separate domain/business logic from presentation, I/O, and storage.
- Deconstruct bloated units: If 1 component, class, or function is too long or handles multiple concerns, immediately break it down into smaller, atomic subcomponents/services with single responsibilities.
- Apply the **Dependency Injection (DI)** pattern: Depend upon abstractions/interfaces, never tight couplings. Pass dependencies via constructors or framework-provided DI containers.

## 2. Framework Conventions First
- When a framework already establishes architectural conventions (e.g. FastAPI, NestJS, Next.js, Django, Go idiomatic layouts, Rust idiomatic traits), always prioritize the framework's native conventions and patterns over ad-hoc custom designs.

## 3. Parallelizable & Hermetic Testing
- Always design tests to be executable in parallel (e.g. `pytest -n auto`, `cargo test`, `go test -parallel`).
- Tests must be stateless and hermetic:
  - No shared mutable globals or static state.
  - Mock external network calls and I/O using DI contracts.
  - Use isolated temporary directories or isolated test transactions.

## 4. AST & CodeGraph Exploration (Blast Radius Analysis)
- Prioritize using CodeGraph / AST exploration before modifying, refactoring, or extending code.
- Analyze callers, callees, symbol references, and downstream dependencies to understand the blast radius and potential regressions.
- A built-in AST impact tool is available at:
  `python3 ~/.gemini/config/skills/craftsman-coder/scripts/codegraph_impact.py <path> --symbol <symbol_name>`

## 5. Deterministic Static Code Analysis for SRP & Abstractions
- In any coding repository, always prioritize setting up and executing **deterministic static code analysis tools** to verify:
  1. **SRP Violations**: Classes/components exceeding line limits (e.g. > 180 lines) or functions exceeding length limits (e.g. > 50 lines). Decompose them into cohesive subcomponents.
  2. **Abstraction Bypasses**: Bypassing abstractions (e.g. direct raw SQL, direct HTTP calls inside UI or business logic instead of repositories/client interfaces).
- Static analysis is preferred whenever possible to ensure deterministic, reproducible verification without subjective guessing.
- A built-in static SRP & abstraction analyzer is available at:
  `python3 ~/.gemini/config/skills/craftsman-coder/scripts/static_srp_analyzer.py <path> [--strict]`

## 6. "Old Coder" Evidence-First Methodology
- All skill rules and workflows are tightly anchored to the "Old Coder" philosophy:
  > *"Review evidence, not code."*
- Follow the 4-phase loop:
  1. **Spec & AST Impact**: Define requirements and check blast radius before writing code.
  2. **TDD Loop**: RED (failing test) -> GREEN (minimal implementation) -> REFACTOR.
  3. **The Gauntlet**: Automated verification via Deterministic Static Analysis + Linters + Typecheck + Parallel Test Suite.
  4. **Evidence Delivery**: Provide terminal execution output as concrete proof of correctness.

## 7. Global Reusable Skill & Tool Extraction
- When identifying repeating patterns in information-seeking or workflow automation, package them into global, repo-agnostic skills and tools (`~/.gemini/config/skills/`) so they can be reused across projects.

## 8. Centralized Secret Management (Infisical Universal Auth)
- When secrets/credentials are required across environments or deployments, **never hardcode or save secrets to git**. Always inject them via Infisical.
- **Machine Identity Setup:**
  - **Vault:** `infisical vault set file`
  - **Domain:** `https://secrets.dvlpid.my.id/api` (or custom endpoint)
  - **Project ID:** `f13379e0-9661-4f8e-81ef-0e81d1502da1`
  - **Environment:** `dev`
  - Authenticate using Universal Auth:
    ```bash
    infisical login --domain https://secrets.dvlpid.my.id/api \
      --method=universal-auth \
      --client-id="$INFISICAL_CLIENT_ID" \
      --client-secret="$INFISICAL_CLIENT_SECRET"
    ```
- **Execution Patterns:**
  - View all secrets:
    `infisical secrets --projectId f13379e0-9661-4f8e-81ef-0e81d1502da1 --env dev`
  - Run commands with injected secrets:
    `infisical run --projectId f13379e0-9661-4f8e-81ef-0e81d1502da1 --env dev -- <command>`
  - Restore AGY CLI OAuth Token:
    `mkdir -p ~/.gemini/antigravity-cli && infisical secrets get AINA_AGY_OAUTH_TOKEN_JSON --projectId f13379e0-9661-4f8e-81ef-0e81d1502da1 --env dev --plain > ~/.gemini/antigravity-cli/antigravity-oauth-token`

## 9. Best Practices for AI-Agent-Ready CLI Tools & Skills
When building or recommending tools and skills for AI agents:
1. **Machine-Readability First:** Always provide `--json` output, deterministic exit codes (0 = success, non-zero = typed failure), and eliminate ANSI formatting/spinners when piped.
2. **Zero Interactivity:** Never block on `stdin` or interactive prompts (`[y/N]`). Always support `--yes`, `--force`, `--non-interactive`, and environment variable fallbacks.
3. **Safety by Design:** Provide `--dry-run` for state-mutating actions, ensure operations are idempotent, and return self-describing actionable errors.
4. **Predictable Noun-Action Structure:** Structure subcommands as `tool <noun> <action>` with rich, parseable `--help` text including concrete examples.

## 10. Fallback Architecture: Vertical Slice Architecture (VSA) + SOLID + EIP
- Whenever a repository or project lacks an established framework architectural convention, **always adopt Vertical Slice Architecture (VSA) coupled with SOLID principles and Enterprise Integration Patterns (EIP)**:
  - Organize by business features/capabilities (`features/<feature_name>/`) utilizing the Request-Endpoint-Response (REPR) pattern, rather than horizontal technical layers.
  - Implement Enterprise Integration Patterns inside slices: Command/Query Routers (Mediator pattern), Pipes & Filters (pipeline middleware), Idempotent Receivers, and Domain Event Pub/Sub for inter-slice communication.

## 11. Real-Time Web Research & Optimal Big-O Complexity
- Always choose algorithm and data structure patterns with the **most optimal Big-O time and space complexity**:
  - Prefer $O(1)$ lookups (hash maps/sets) over $O(N)$ linear scans.
  - Avoid $O(N^2)$ nested loops; favor $O(N \log N)$ sorting or indexed heaps/trees.
  - Use memory-efficient streaming $O(1)$ space rather than buffering large payloads in memory.
- **Mandatory Web Research:** Never rely solely on pre-trained assumptions as knowledge may be outdated. **Always research the web per the current month and year** to discover state-of-the-art algorithmic patterns, optimal data structures, and latest high-performance library implementations.

## 12. High-Performance, Low-RAM Libraries & Enterprise License Compliance
- **Peak Performance & Minimal RAM:** Always select modern, cache-friendly, zero-copy, and memory-efficient open-source libraries (e.g. `orjson`/`msgspec`, `polars`, `sonic`, `zerolog`, `simd-json`, `fast-json-stringify`).
- **Permissive Enterprise Licensing:**
  - Prioritize permissive licenses: **MIT, Apache 2.0, BSD-2-Clause, BSD-3-Clause, ISC**.
  - **Default Deny for Copyleft:** Strictly avoid strong copyleft (`GPLv2/v3`) and network copyleft (`AGPLv3`, `SSPL`) in commercial/enterprise projects to prevent source disclosure liability during enterprise audits.

## 13. Mandatory VSA Boundary Enforcement & Repository-Level GEMINI.md
- **Deterministic VSA Boundary Enforcement:** When a repo implements VSA, always set up a deterministic architectural linter (e.g. `dependency-cruiser` for JS/TS, `import-linter` for Python, `depguard` for Go, or `vsa_boundary_checker.py`) to forbid cross-slice direct imports.
- **Mandatory Repository-Level `GEMINI.md`:**
  - Whenever initializing or structuring any repository, **always create a `GEMINI.md` at the repository root** to persist architectural choices, slice rules, and verification commands.
  - **Strict Portability & Anti-Leak Rule:** Because repo-level `GEMINI.md` is committed and pushed to git, it **MUST NOT reference anything outside the repository** (no local paths like `~/.gemini/...` or `/data/data/...`, no machine-specific environments or credentials). It must remain 100% self-contained, portable, and reproducible for any team member or CI runner.

## 14. Dual-Tier Verification & Repository-Level Technical Debt Ledgers
- **Separation of Global Tooling vs Repository-Level Ledgers:**
  - Global tools (e.g. `detect-mocks`, `static-srp-analyzer`, `craftsman-coder`) enforce universal AST invariant rules and parsers. They must **NEVER** store project-specific exemptions or machine-local states.
  - Project-specific exemptions, cited technical debts, and temporary hardware/upstream blockers MUST live **100% inside the project repository** (e.g., `docs/TECHNICAL_DEBT.md`, `docs/dev/debt/<modul>.md`, or `.zero-mock-allowlist.json`).
- **Fail-Fast Throw by Default (Zero Silent Fallbacks):**
  - Unimplemented trait methods, interface contracts, or unverified hardware paths MUST throw explicit typed errors (`throw NotImplementedError()`, `todo!()`, `unimplemented!()`), **NEVER** silent stubs returning dummy successes (`return 0`, `return true`, `Ok(())`, `return None`).
- **Citation Contract for Every Ledger Exemption:**
  - Every exemption registered in the repo-level debt ledger must cite a concrete ground truth: issue ID, external RFC, hardware silicon measurement, or upstream blocker.
- **Zero Agent Note & Scratch Pollution:**
  - Never commit temporary agent scratch files (`notes.md`, `agent_notes.*`, `scratch_*.py`, `temp_*.py`, `*.log`) to production directories.
- **Zero Rationalizing Comments:**
  - Prohibit comments attempting to rationalize fake/mock behavior (e.g. `// assume success for now`, `// dummy mock for testing`, `// fake return`). Real evidence (tests, measurements, ledger) must replace rationalizing comments.

## 15. Dependency Security & Pre-Commit CVE Gate (Google OSV-Scanner)
- **Zero Known CVEs Policy:** Whenever modifying or adding dependencies (`composer.json`, `package.json`, `requirements.txt`, `poetry.lock`, `uv.lock`, `go.mod`, `Cargo.toml`, `pom.xml`, etc.), agents must run `osv-scanner-gate --staged` or `osv-scanner scan source <path>` before committing.
- **Guided Remediation First:** If vulnerabilities are found, resolve them via `osv-scanner fix` or explicit package upgrade to non-vulnerable versions.
- **Audited Exemptions via osv-scanner.toml:** If a vulnerability cannot be updated immediately due to upstream constraints, it MUST be formally recorded in the repository's `osv-scanner.toml` under `[[IgnoredVulns]]` with a strict `ignoreUntil` date and rationale. Never bypass security gates silently.
