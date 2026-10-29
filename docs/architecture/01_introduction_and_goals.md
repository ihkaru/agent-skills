# 1. Pengantar dan Tujuan (Introduction and Goals)

> [!INFO] **Architecture Provenance & Freshness**
> - **Verified Commit**: `b81c7a3` (branch: `main`)
> - **Verified Timestamp**: `2026-10-29T14:04:00+07:00`
> - **Tracked Paths**: `skills/`, `config/`, `install.sh`
> - **Drift Status**: `verified`

Dokumen ini menjelaskan arsitektur dan prinsip rekayasa perangkat lunak dari repositori **`agent-skills`** (`ihkaru/agent-skills`). Repositori ini berfungsi sebagai hub konfigurasi terpadu, penyedia *custom skills*, dan penyedia kakas inspeksi statis deterministik untuk **Antigravity CLI (AGY)** dan agen pengodean otonom (*AI coding agents*).

---

## 1.1 Masalah Nyata yang Diselesaikan

Dalam era pengembangan perangkat lunak berbasis AI (*AI-assisted / agentic coding*), model bahasa besar (LLM) sering kali menghasilkan kode dengan beberapa kelemahan kritis:
1. **Halusinasi & Asumsi Tanpa Bukti (*Ungrounded Assumptions*)**: Agen cenderung mengasumsikan keberadaan API, file, atau schema tanpa melakukan verifikasi pembacaan codebase nyata.
2. **Solusi Instan Dangkal (*Quick Hacks & Silent Mocks*)**: Agen sering membuat tiruan palsu (*mock/dummy stubs*), *fake latency*, atau pengabaian error (*silent fallbacks*) di jalur produksi untuk mempercepat penyelesaian tugas secara semu.
3. **Pembengkakan Komponen (*SRP Violation*)**: Agen kerap menumpuk ratusan baris kode logika bisnis, presentasi, dan akses database mentah ke dalam satu file tunggal yang monolitik.
4. **Kebocoran Celah Keamanan Dependensi (*Dependency CVEs*)**: Agen menambahkan package atau memperbarui manifest dependensi tanpa memverifikasi database kerentanan terbuka (*Open Source Vulnerabilities*).
5. **Pembusukan Arsitektur (*Architecture Drift*)**: Dokumentasi sistem yang dibuat di awal proyek cepat menjadi usang (*stale*) karena tidak terikat langsung dengan riwayat commit Git aktual.

**`agent-skills`** mengatasi masalah ini dengan menyediakan rangkaian aturan universal (`GEMINI.md`), panduan disiplin rekayasa (*Old Coder methodology*), dan kakas verifikasi mandiri berbasis AST statis yang berjalan di terminal lokal sebelum perubahan di-commit.

---

## 1.2 Sasaran Mutu Utama (Quality Goals)

Sasaran mutu arsitektur `agent-skills` dirumuskan menggunakan model kualitas Q42:

| Prioritas | Tag Mutu | Sasaran Mutu | Arti Nyata bagi Pengguna & Agen AI |
|:---:|:---|:---|:---|
| 1 | #correctness | Verifikasi Deterministik & Anti-Mock | Pengujian dan inspeksi statis menghasilkan bukti riil; tidak ada kode mock liar, stub kosong, atau asumsi teoretis yang lolos ke produksi. |
| 2 | #performance | Operasi Cepat & Footprint RAM Minimal | Kakas CLI selesai dieksekusi dalam hitungan milidetik; mode `--staged` selesai <0.05s jika tidak ada manifest yang dimodifikasi; pemindaian CVE sangat ringan tanpa unduh database raksasa. |
| 3 | #maintainability | Dekomposisi Modular & SOLID Berkelanjutan | Kode terorganisasi dalam *single responsibility units*, arsitektur *vertical slices*, serta dokumentasi arc42 modular 12-bagian yang mudah dipahami agen tanpa kehabisan token. |
| 4 | #security | Zero Known CVEs & Sanitasi Secret | Bebas dari kerentanan dependensi via Google OSV-Scanner; kredensial disuntikkan secara runtime melalui Infisical tanpa hardcode di Git. |
| 5 | #usability | Antarmuka Agen-Siap & Zero-Interactivity | Setiap kakas CLI mendukung format mesin `--json`, kode keluar bertipe (*typed exit codes*), mode non-interaktif tanpa prompt manual, dan instalasi *one-command bootstrap*. |

---

## 1.3 Pemangku Kepentingan (Stakeholders)

| Peran | Harapan Terhadap Sistem |
|:---|:---|
| **Autonomous AI Agents (Antigravity)** | Memperoleh panduan operasional terstruktur (*skills*), aturan perilaku universal, dan kakas verifikasi terminal dengan format `--json`. |
| **Software Engineers & Lead Architects** | Memastikan seluruh kode yang dihasilkan agen mematuhi standar enterprise (SOLID, SRP, Clean Architecture, zero-mock, dan aman dari CVE). |
| **DevOps & CI/CD Pipeline** | Menjalankan *gatekeeper* pra-commit dan otomatisasi build tanpa overhead unduhan database CVE monolitik atau dependensi runtime yang berat. |
