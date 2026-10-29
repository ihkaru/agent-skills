# 4. Strategi Solusi (Solution Strategy)

> [!INFO] **Architecture Provenance & Freshness**
> - **Verified Commit**: `e284acb` (branch: `main`)
> - **Verified Timestamp**: `2026-10-29T12:54:18+07:00`
> - **Tracked Paths**: `skills/`, `config/`, `install.sh`
> - **Drift Status**: `verified`

Dokumen ini menguraikan keputusan strategi arsitektur fundamental yang diadopsi untuk memastikan repositori `agent-skills` memenuhi seluruh sasaran kualitas yang ditetapkan pada Bagian 1.

---

## 4.1 Ringkasan Strategi Arsitektur Utama

| Sasaran Kualitas | Keputusan Strategi Arsitektur | Rationale & Dampak |
|:---|:---|:---|
| **#correctness** | **Metodologi Evidence-First ("Old Coder") & Dual-Tier Verification** | Menolak klaim teoretis agen; mewajibkan verifikasi bukti eksekusi terminal (exit code 0, log eksekusi riil, unit test hermetis). Pengecualian sementara dilarang disimpan di global tooling, melainkan wajib dicatat formal dalam debt ledger repositori (`docs/TECHNICAL_DEBT.md` atau `osv-scanner.toml`). |
| **#performance** | **Bypass Staged Files & Kueri API Terdistribusi** | Kakas pra-commit (`osv-scanner-gate --staged`, `arc42-pre-commit`) memeriksa `git diff --cached` terlebih dahulu. Jika file relevan tidak dimodifikasi, operasi langsung lulus dalam <0.05s. Menggunakan OSV.dev batch API daripada mengunduh database CVE ratusan MB ke disk. |
| **#maintainability** | **Modular arc42 & Arsitektur Vertical Slices** | Memecah dokumentasi arsitektur ke dalam 12 file independen (`01_` hingga `12_`) dan mengarahkan kode proyek ke Vertical Slice Architecture (VSA) dengan linter batas modular (`vsa_boundary_checker.py`), meminimalkan *cognitive load* dan batasan context window agen LLM. |
| **#security** | **JIT Runtime Secret Injection & Pre-Commit CVE Gate** | Mengeliminasi penyimpanan password, private key, dan token di git atau file `.env` lokal dengan memanfaatkan Infisical Universal Machine Auth; memblokir commit yang membawa library rentan via `osv-scanner-gate`. |
| **#usability** | **Zero-Dependency CLI & Universal Installer One-Liner** | Seluruh skrip pembantu dibangun murni menggunakan Python Standard Library. Distribusi dilakukan via `install.sh` yang idempoten dan langsung menautkan biner ke `~/.local/bin` tanpa kompilasi manual rumit. |

---

## 4.2 Pola Desain Kunci yang Diterapkan

### 1. Pola Gatekeeper Pra-Commit Non-Intrusif (*Short-Circuit Staged Gate*)
Untuk menjaga developer experience (DX) tetap menyenangkan dan cepat, kakas verifikasi menerapkan pola *Short-Circuit*:
```text
Git Commit Invocation
       │
       ▼
Git Staged Inspection (git diff --cached --name-only)
       │
       ├─── [Tidak ada Manifest/Doc Relevan] ───► EXIT 0 (Bypass dalam <0.05s)
       │
       └─── [Manifest/Doc Relevan Berubah] ────► Eksekusi Scan Presisi ──► Lulus/Gagal
```

### 2. Pola Arsitektur Hidup (*Living Architecture Provenance*)
Dokumentasi bukan berkas statis yang mati. Dengan menyematkan commit hash dan timestamp terverifikasi di header setiap dokumen:
- Linter `arc42-lint` dapat membandingkan commit baseline dengan `HEAD` Git secara matematis.
- Jika source code berubah lebih dari batas toleransi (*drift threshold* = 15 commit) tanpa pembaruan dokumen arsitektur, commit diblokir secara otomatis.

### 3. Pola Dual-Tier Verification (Global Invariant vs Local Debt Ledger)
- **Tingkat Global (Alat & Aturan)**: Kakas seperti `detect-mocks` dan `osv-scanner-gate` bersikap tidak kenal kompromi (*strict AST invariant*), menolak mock dan dummy stubs di jalur produksi.
- **Tingkat Repositori (Debt Ledger)**: Jika ada batasan perangkat keras nyata, bug upstream framework, atau integrasi pihak ketiga yang belum selesai, pengecualian dicatat secara jujur dan transparan di dalam repositori bersangkutan (`docs/TECHNICAL_DEBT.md` atau `osv-scanner.toml`) lengkap dengan tanggal batas kedaluwarsa (`ignoreUntil`).
