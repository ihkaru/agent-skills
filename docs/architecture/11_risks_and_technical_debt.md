# 11. Risiko dan Hutang Teknis (Risks and Technical Debt)

> [!INFO] **Architecture Provenance & Freshness**
> - **Verified Commit**: `7ed205b` (branch: `main`)
> - **Verified Timestamp**: `2026-10-29T13:02:00+07:00`
> - **Tracked Paths**: `skills/`, `config/`, `install.sh`
> - **Drift Status**: `verified`

Dokumen ini mencatat matriks risiko arsitektur dan buku besar hutang teknis (*technical debt ledger*) untuk memastikan transparansi dan pengelolaan berkelanjutan.

---

## 11.1 Matriks Risiko Arsitektur (Architectural Risk Matrix)

Berikut adalah daftar risiko yang diidentifikasi dari Keputusan Arsitektur (ADR-01 hingga ADR-04 pada Bagian 9):

| ID Risiko | Sumber Keputusan | Deskripsi Potensi Risiko | Dampak & Mitigasi yang Diterapkan |
|:---|:---|:---|:---|
| RISK-01 | ADR-01 (Living Architecture Drift) | Pemblokiran commit darurat (*hotfix blocker*) ketika pengembang harus segera merilis perbaikan cepat tanpa sempat menyelaraskan dokumen arsitektur. | **Dampak: Sedang**. **Mitigasi**: Tersedia mekanisme darurat resmi melalui variabel lingkungan `SKIP_ARC42_LINT=1 git commit` atau flag git bawaan `git commit --no-verify`. |
| RISK-02 | ADR-02 (Pure Python Stdlib AST) | Keterbatasan kedalaman parsing AST saat menganalisis sintaksis kompleks pada bahasa dinamis seperti PHP, Rust, atau Java tanpa AST compiler resmi masing-masing bahasa. | **Dampak: Rendah**. **Mitigasi**: Mengombinasikan tokenisasi regex terstruktur dengan pemeriksaan import patterns, serta memfokuskan analisis mendalam pada struktur kelas dan batasan baris fungsi. |
| RISK-03 | ADR-03 (OSV.dev Network Batch API) | Ketergantungan pada koneksi internet publik (`api.osv.dev`) saat memindai manifest atau lockfile yang baru saja di-*stage*. | **Dampak: Sedang**. **Mitigasi**: Jika berada di jaringan terisolasi (*air-gapped*), OSV-Scanner mendukung flag `--offline` dengan database lokal yang diunduh sebelumnya melalui `osv-scanner --download-offline-databases`. |
| RISK-04 | ADR-04 (Staged Mode Short-Circuit) | Potensi celah kerentanan terlewatkan apabila pengembang memodifikasi dependensi di direktori kerja tetapi mengabaikan lockfile saat melakukan commit. | **Dampak: Rendah**. **Mitigasi**: Pipa CI/CD server tetap menjalankan pemindaian penuh terhadap seluruh repositori (`osv-scanner-gate --path .`) pada saat pull request dibuka. |

---

## 11.2 Buku Besar Hutang Teknis (Technical Debt Ledger)

| ID Hutang | Area Komponen | Uraian Hutang Teknis | Rencana Remediasi & Target |
|:---|:---|:---|:---|
| **DEBT-01** | OSV-Scanner Gate | Call analysis saat ini hanya didukung untuk Go dan Rust melalui compiler eksternal (`--call-analysis go,rust`). Belum tersedia untuk ekosistem PHP dan Node.js. | Menunggu rilis upstream engine OSV-SCALIBR Google untuk dukungan *call graph* JavaScript dan PHP. |
| **DEBT-02** | VSA Boundary Checker | Konfigurasi batas slice (`.vsa-boundaries.json`) saat ini masih didefinisikan secara manual di level proyek pengguna dan belum terbuat secara otomatis saat inisialisasi repositori baru. | Menambahkan subperintah `vsa-boundary-checker --init` untuk melakukan *scaffolding* berkas konfigurasi awal. |
| **DEBT-03** | ThinkStation Coolify CLI | Otomatisasi rotasi token SSH Infisical masih memerlukan sinkronisasi manual jika masa aktif kredensial mesin identity kedaluwarsa setelah 30 hari. | Menyediakan cron job latar belakang otomatis untuk memperbarui session token sebelum kedaluwarsa. |
