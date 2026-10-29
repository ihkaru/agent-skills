# 10. Persyaratan Mutu (Quality Requirements)

> [!INFO] **Architecture Provenance & Freshness**
> - **Verified Commit**: `68c36e2` (branch: `main`)
> - **Verified Timestamp**: `2026-10-29T14:04:00+07:00`
> - **Tracked Paths**: `skills/`, `config/`, `install.sh`
> - **Drift Status**: `verified`

Dokumen ini mendokumentasikan skenario mutu terukur menggunakan pohon kualitas Q42 untuk memvalidasi pemenuhan sasaran mutu Bagian 1.2.

---

## 10.1 Pohon Kualitas (Quality Tree)

```text
Kualitas agent-skills
├── #correctness
│   └── QS-01: Inspeksi AST Tanpa Mock & Verifikasi Deterministik
├── #performance
│   └── QS-02: Eksekusi Pra-Commit Cepat (<0.05s) & Kueri Batch
├── #maintainability
│   └── QS-03: Dokumentasi Modular Anti-Monolith & Pencegahan Drift
├── #security
│   └── QS-04: Gerbang Keamanan Bebas CVE Sebelum Git Commit
└── #usability
    └── QS-05: Antarmuka Agen Siap-Pakai dengan Output JSON & Non-Interaktif
```

---

## 10.2 Skenario Mutu Terukur (Quality Scenarios)

### QS-01: Deteksi Pelanggaran AST dan Mock Palsu
* **Quality Property**: #correctness
* **Stimulus**: Agen atau pengembang menambahkan implementasi baru yang memuat pemanggilan mock (`unittest.mock`), *fake sleep*, atau bypass query mentah.
* **Respon Sistem**: Kakas `detect-mocks` dan `static-srp-analyzer` menganalisis AST kode sumber dalam hitungan milidetik, mengeluarkan daftar baris spesifik yang melanggar, dan mengembalikan exit code `1`.
* **Ukuran Sukses**: 100% pelanggaran terdeteksi secara deterministik; tidak ada silent failure yang lolos tanpa dicatat di ledger hutang teknis.

---

### QS-02: Latensi Eksekusi Pra-Commit Staged Bypass
* **Quality Property**: #performance
* **Stimulus**: Pengembang melakukan `git commit` untuk perubahan kode biasa (tanpa mengubah manifest atau lockfile).
* **Respon Sistem**: Kakas `osv-scanner-gate --staged` mengekstrak file staged melalui `git diff --cached` dan mendeteksi ketiadaan berkas manifest.
* **Ukuran Sukses**: Pemeriksaan selesai dalam waktu **kurang dari 0.05 detik (<50 ms)** dengan exit code `0`, tanpa menjalankan pemindaian jaringan yang tidak perlu.

---

### QS-03: Deteksi Pembusukan Dokumentasi Arsitektur (Architecture Drift)
* **Quality Property**: #maintainability
* **Stimulus**: Perubahan kode sumber terus di-commit pada branch `main` hingga melampaui batas ambang (*drift threshold* = 15 commit) tanpa memperbarui berkas `docs/architecture/`.
* **Respon Sistem**: Kakas `arc42-lint` menghitung jarak commit antara baseline provenance dengan `HEAD` Git.
* **Ukuran Sukses**: Linter memunculkan peringatan atau memblokir commit pra-commit (`arc42-pre-commit`) hingga dokumentasi arsitektur disinkronkan kembali.

---

### QS-04: Pencegahan Kebocoran Kerentanan Dependensi Baru
* **Quality Property**: #security
* **Stimulus**: Perintah `composer require` atau `npm install` menambahkan paket pihak ketiga yang memiliki celah keamanan aktif (CVSS >= 7.0).
* **Respon Sistem**: Kakas `osv-scanner-gate --staged` memindai lockfile yang di-*stage* ke endpoint OSV.dev dan menghentikan proses commit.
* **Ukuran Sukses**: Celah keamanan berhasil diblokir sebelum mencapai remote branch; petunjuk remediasi terarah (`osv-scanner fix`) disajikan ke terminal.

---

### QS-05: Interoperabilitas Otomasi Agen AI (Zero Interactivity & JSON Output)
* **Quality Property**: #usability
* **Stimulus**: Agen Antigravity menjalankan kakas dengan flag `--json` melalui subproses CLI non-interaktif.
* **Respon Sistem**: Kakas mengembalikan payload JSON valid, bebas dari kode warna ANSI, dan tanpa menunggu masukan dari keyboard pengguna (`stdin`).
* **Ukuran Sukses**: Agen berhasil memproses status hasil pengujian dan metadata pelanggaran secara otomatis 100% tanpa hambatan timeout.
