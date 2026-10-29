# 3. Konteks dan Cakupan (Context and Scope)

> [!INFO] **Architecture Provenance & Freshness**
> - **Verified Commit**: `68c36e2` (branch: `main`)
> - **Verified Timestamp**: `2026-10-29T14:04:00+07:00`
> - **Tracked Paths**: `skills/`, `config/`, `install.sh`
> - **Drift Status**: `verified`

Dokumen ini mendefinisikan batasan sistem repositori **`agent-skills`**, membedakan tanggung jawab internal sistem dengan entitas dan antarmuka eksternal di sekitarnya.

---

## 3.1 Diagram Konteks Bisnis & Teknis (Mermaid C4 Context)

```mermaid
C4Context
    title Diagram Konteks Sistem - agent-skills Toolchain Hub
    
    Person(developer, "Developer / Engineer", "Pengembang perangkat lunak yang berkolaborasi dengan AI.")
    Person(agent, "Antigravity AI Agent", "Agen pengodean otonom yang membaca aturan dan mengeksekusi kakas.")
    
    System(agentskills, "agent-skills Toolchain Hub", "Hub panduan skills, aturan perilaku, dan kakas CLI inspeksi statis deterministik.")
    
    System_Ext(osvdev, "Google OSV.dev API", "Database terbuka celah kerentanan dependensi open-source.")
    System_Ext(infisical, "Infisical Secret Vault", "Manajemen kredensial terpusat & Universal Machine Auth.")
    System_Ext(gitrepo, "Git VCS & Hooks", "Sistem kontrol versi lokal dan git pre-commit runner.")
    System_Ext(coolify, "ThinkStation Coolify Server", "Infrastruktur container server mandiri via Tailscale.")

    Rel(developer, agentskills, "Memasang & menjalankan kakas via terminal", "CLI")
    Rel(agent, agentskills, "Membaca SKILL.md dan memanggil kakas verifikasi", "CLI / JSON")
    Rel(agentskills, gitrepo, "Memeriksa status staged & riwayat commit", "IF-05: Git CLI")
    Rel(agentskills, osvdev, "Batch HTTP query celah CVE dependensi", "IF-03: HTTPS / REST")
    Rel(agentskills, infisical, "Mengambil secret dan token SSH", "IF-02: REST API")
    Rel(agentskills, coolify, "Menginspeksi log & query database container", "IF-04: SSH over Tailscale")
    Rel(agentskills, agent, "Menyajikan hasil verifikasi deterministik", "IF-01: JSON / Stdout")
```

---

## 3.2 Antarmuka Eksternal Sistem (External Interfaces)

Berikut adalah daftar antarmuka formal yang menghubungkan komponen internal `agent-skills` dengan ekosistem luar:

| ID Interface | Nama Antarmuka | Protokol / Format | Deskripsi & Komponen Pengguna |
|:---|:---|:---|:---|
| IF-01 | Antigravity CLI / AGY Runner Interface | Process execution / JSON / Stdout | Antarmuka pemanggilan kakas CLI (`static-srp-analyzer`, `codegraph-impact`, `vsa-boundary-checker`, `detect-mocks`, `arc42-lint`, `osv-scanner-gate`) oleh IDE atau AGY agent. |
| IF-02 | Infisical Universal Auth API | HTTPS / JSON REST API | Antarmuka autentikasi mesin terpusat untuk injeksi secret runtime dan provisi SSH key tanpa menyimpan password di disk lokal. |
| IF-03 | Google OSV.dev Batch Vulnerability API | HTTPS / JSON REST API (HTTP/2) | Antarmuka kueri batch terdistribusi untuk mengecek *package hash* dan versi manifest terhadap database CVE terbuka di `api.osv.dev`. |
| IF-04 | Tailscale Mesh & SSH Transport | Encrypted WireGuard / SSH Protocol | Antarmuka transportasi aman untuk manajemen kontainer Coolify dan query database jarak jauh (`*.dvlpid.my.id`). |
| IF-05 | Git VCS & Pre-Commit Hook Runner | Git Native CLI / Hook Subprocess | Antarmuka integrasi pra-commit untuk memeriksa *staged files*, menghitung jarak commit *drift*, dan memvalidasi integritas sebelum commit. |
