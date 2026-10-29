# 2. Batasan Arsitektur (Architecture Constraints)

> [!INFO] **Architecture Provenance & Freshness**
> - **Verified Commit**: `7ed205b` (branch: `main`)
> - **Verified Timestamp**: `2026-10-29T13:02:00+07:00`
> - **Tracked Paths**: `skills/`, `config/`, `install.sh`
> - **Drift Status**: `verified`

Dokumen ini mendokumentasikan batasan teknis, batasan organisasi, dan konvensi ekosistem yang mengikat pengembangan repositori `agent-skills`.

---

## 2.1 Batasan Teknis (Technical Constraints)

| ID | Batasan | Alasan dan Dampak Arsitektur |
|:---|:---|:---|
| **CON-01** | **Python Standard Library Mandiri (*Zero External Python Dependencies*)** | Seluruh skrip CLI inti (`static_srp_analyzer.py`, `codegraph_impact.py`, `vsa_boundary_checker.py`, `arc42-lint.py`, `osv_scanner_gate.py`, `main.py` detector) **HANYA menggunakan pustaka bawaan Python 3.9+** (`argparse`, `ast`, `json`, `subprocess`, `pathlib`, `re`, `shutil`). Menghindari kebutuhan `pip install` atau konflik virtual environment saat dibootstrap di lingkungan baru. |
| **CON-02** | **Biner Eksternal Ringan Berlisensi Permisif** | Kakas eksternal yang diadopsi harus berupa biner Go/Rust terkompilasi mandiri (misal Google `osv-scanner`) atau utilitas sistem standar (`git`, `curl`, `bash`). Dilarang mengadopsi kakas dengan dependensi runtime berat seperti JVM atau Node.js jika ada alternatif biner mandiri. |
| **CON-03** | **Portabilitas Sistem Operasi & Lokasi Instalasi** | Skrip installer `install.sh` harus berjalan mulus pada distribusi Linux modern (khususnya Arch/CachyOS, Debian/Ubuntu) serta macOS, mengarahkan symlink CLI ke `${HOME}/.local/bin` untuk eksekusi tanpa hak root (`non-root user space`). |
| **CON-04** | **Standar Lisensi Perusahaan (Permissive Only)** | Seluruh kode dalam repositori ini dilisensikan di bawah **MIT License**. Tidak diperkenankan mengadopsi komponen berlisensi copyleft keras (GPLv2/v3, AGPLv3) yang dapat memicu tuntutan *source disclosure* saat diaudit di lingkungan enterprise. |

---

## 2.2 Batasan Desain Antarmuka Agen (AI-Agent-Ready CLI Constraints)

Berdasarkan Tenet 9 Panduan Global, semua kakas CLI yang dihasilkan repositori ini tunduk pada batasan berikut:
1. **Zero Interactivity**: Dilarang memblokir `stdin` dengan pertanyaan interaktif (`[y/N]`). Semua operasi harus mendukung flag otomatisasi atau default non-interaktif.
2. **Deterministic Exit Codes**:
   - `0`: Sukses tanpa temuan / operasi valid.
   - `1`: Pelanggaran terdeteksi (misal: CVE ditemukan, mock terdeteksi, arsitektur *drift* melampaui ambang batas).
   - `2`: Kesalahan sistem atau parameter tidak valid (misal: biner tidak ditemukan).
3. **Machine-Readable First**: Selalu menyediakan flag `--json` yang menghasilkan format payload terstruktur tanpa polusi ANSI terminal codes atau spinner animasi ketika dipipa (*piped*).
4. **Idempotent Operations**: Pemasangan symlink (`ln -sf`), pembaruan file konfigurasi, dan pembuatan direktori harus aman dijalankan berulang kali tanpa merusak state sistem.

---

## 2.3 Batasan Organisasi & Standar Dokumentasi

| ID | Batasan Organisasi | Penjelasan |
|:---|:---|:---|
| **CON-05** | **Modular Numbered Files (arc42 Standard)** | Dokumentasi arsitektur dilarang dibuat sebagai satu file markdown monolitik raksasa. Wajib dipecah menjadi berkas bernomor `01_` hingga `12_` di `docs/architecture/`. |
| **CON-06** | **Git Provenance Mandatory Callout** | Setiap berkas dokumentasi arsitektur wajib memuat blok metadata provenance commit SHA, timestamp, dan path terawasi di awal dokumen untuk memfasilitasi audit drift otomatis oleh `arc42-lint`. |
| **CON-07** | **Zero Scratch File Pollution** | Dilarang menyimpan file sementara agen (`notes.md`, `scratch_*.py`, file log ad-hoc) di dalam direktori produksi kode sumber. |
