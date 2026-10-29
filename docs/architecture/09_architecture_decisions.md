# 9. Keputusan Arsitektur (Architecture Decisions - ADR)

> [!INFO] **Architecture Provenance & Freshness**
> - **Verified Commit**: `68c36e2` (branch: `main`)
> - **Verified Timestamp**: `2026-10-29T14:04:00+07:00`
> - **Tracked Paths**: `skills/`, `config/`, `install.sh`
> - **Drift Status**: `verified`

Dokumen ini mendokumentasikan Rekam Jejak Keputusan Arsitektur (*Architectural Decision Records* - ADR) yang signifikan secara struktural dalam pembentukan sistem `agent-skills`.

---

### ADR-01: Standardisasi Living Architecture & Git Provenance Callout

* **Konteks**: Dokumentasi arsitektur tradisional cepat membusuk (*architecture drift*) karena tidak memiliki penanda waktu atau tautan commit yang dapat diverifikasi oleh pipeline otomatis.
* **Keputusan**: Mewajibkan format modular 12-file arc42 dan menuntut blok `Architecture Provenance & Freshness` di setiap awal berkas markdown. Mengembangkan linter `arc42-lint` untuk memeriksa jarak commit secara otomatis.
* **Konsekuensi Positif**: Dokumentasi selalu terikat dengan versi kode aktual; agen AI dapat langsung mengetahui apakah arsitektur masih valid atau telah basi.
* **Risks Created**: RISK-01

---

### ADR-02: Pustaka Standar Python Murni untuk Kakas Verifikasi Inti

* **Konteks**: Kakas CLI yang mengandalkan pustaka pihak ketiga (`pip install pydantic`, `rich`, `networkx`) sering mengalami kegagalan di mesin pengembang baru atau CI environment karena konflik virtualenv atau ketiadaan koneksi internet saat instalasi.
* **Keputusan**: Menulis seluruh parser AST, boundary checker, detector mock, dan linter menggunakan pustaka bawaan Python (`ast`, `re`, `argparse`, `json`, `subprocess`).
* **Konsekuensi Positif**: Proses bootstrap berlangsung seketika tanpa `pip install`; instalasi berjalan mulus di CachyOS, Ubuntu, Debian, Alpine, maupun macOS.
* **Risks Created**: RISK-02

---

### ADR-03: Kueri Batch OSV.dev Terdistribusi Dibandingkan Database CVE Monolitik

* **Konteks**: Scanner kerentanan tradisional seperti Trivy atau Grype mengharuskan pengunduhan snapshot database CVE ratusan megabyte ke disk lokal sebelum dapat melakukan pemindaian pertama, memicu kelambatan ekstrem pada pre-commit hook dan CI ephemeral runner.
* **Keputusan**: Mengadopsi **Google OSV-Scanner** yang menggunakan Batch Query HTTP/2 ke `api.osv.dev` dengan payload commit hashes/package version.
* **Konsekuensi Positif**: Pemindaian selesai dalam hitungan 1–3 detik; footprint memori sangat kecil; mendukung lebih dari 10 ekosistem bahasa pemrograman secara *agnostic*.
* **Risks Created**: RISK-03

---

### ADR-04: Bypass Staged Files pada Gatekeeper Pra-Commit

* **Konteks**: Memindai seluruh repositori raksasa pada setiap kali developer menjalankan `git commit` menimbulkan latensi yang mengganggu ritme kerja (*friction*).
* **Keputusan**: Menerapkan mode `--staged` pada `osv-scanner-gate` dan `arc42-pre-commit`. Jika tidak ada manifest atau file sumber relevan yang di-*stage*, gatekeeper langsung keluar dengan exit code `0` dalam waktu kurang dari 50 milidetik.
* **Konsekuensi Positif**: Developer experience (DX) tetap sangat responsif; pemindaian mendalam hanya terjadi ketika ada perubahan dependensi atau arsitektur nyata.
* **Risks Created**: RISK-04
