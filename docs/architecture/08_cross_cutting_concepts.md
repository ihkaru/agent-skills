# 8. Konsep Lintas-Sektoral (Cross-Cutting Concepts)

> [!INFO] **Architecture Provenance & Freshness**
> - **Verified Commit**: `68c36e2` (branch: `main`)
> - **Verified Timestamp**: `2026-10-29T14:04:00+07:00`
> - **Tracked Paths**: `skills/`, `config/`, `install.sh`
> - **Drift Status**: `verified`

Dokumen ini mendokumentasikan pola, mekanisme, dan pendekatan menyeluruh yang diterapkan secara seragam di seluruh modul repositori `agent-skills`.

---

## 8.1 Standar Kode Keluar Deterministik (*Deterministic Exit Codes*)

Setiap alat CLI (`static-srp-analyzer`, `arc42-lint`, `detect-mocks`, `osv-scanner-gate`, `vsa-boundary-checker`) wajib mematuhi konvensi status exit code berikut:

| Exit Code | Makna / Kondisi | Respon Sistem / Agen AI |
|:---:|:---|:---|
| `0` | **BERHASIL / CLEAN**: Tidak ada pelanggaran arsitektur, tidak ada celah CVE, atau bypass staged files aktif. | Agen diizinkan melanjutkan langkah berikutnya atau melakukan commit. |
| `1` | **PELANGGARAN TERDETEKSI**: Ditemukan CVE, pelanggaran SRP, mock ilegal, atau arsitektur *drift* melampaui batas. | Agen wajib memperbaiki masalah atau mencatat pengecualian terverifikasi di debt ledger repositori. |
| `2` | **KESALAHAN SISTEM / ARGUMEN**: Biner pendukung tidak ditemukan di PATH, argumen CLI tidak valid, atau syntax error. | Agen memeriksa pesan stderr dan memperbaiki konfigurasi lingkungan. |

---

## 8.2 Manajemen Kredensial & Sanitasi Secret (Infisical Universal Auth)

Sesuai aturan global Tenet 8, repositori dan seluruh kakas yang dihasilkan memiliki kebijakan tegas:
- **Dilarang Menyimpan Secret di Git**: File `.env`, private SSH key, atau database password dilarang di-commit ke Git.
- **Injeksi Saat Runtime**: Akses ke server produksi atau database dilakukan secara JIT (*Just-In-Time*) dengan mengambil token terenkripsi dari Infisical:
  ```bash
  infisical run --projectId f13379e0-9661-4f8e-81ef-0e81d1502da1 --env dev -- <command>
  ```
- **Portabilitas GEMINI.md**: File `GEMINI.md` yang diletakkan di root repositori proyek **HARUS 100% bebas dari path lokal mesin (`~/.gemini/...`)** dan kredensial privat agar dapat di-push dengan aman ke remote repositori publik/organisasi.

---

## 8.3 Pengujian Hermetis & Bebas Jaringan (*Hermetic Parallel Testing*)

Seluruh unit test di dalam `skills/*/tests/` dirancang dengan prinsip:
1. **Zero External Network**: Pengujian tidak boleh melakukan kueri internet langsung; kueri subprocess atau API eksternal diisolasi menggunakan mock struktural di lapisan pengujian.
2. **Stateless & Parallel-Ready**: Pengujian tidak menggunakan state mutable global, aman dijalankan secara paralel (`pytest -n auto` atau multi-runner).
3. **Eksekusi Seketika**: Seluruh rangkaian unit test alat harus selesai dalam waktu kurang dari 1 detik.

---

## 8.4 Penanganan Eksepsi Tanpa Kegagalan Senyap (*Zero Silent Fallbacks*)

Mengikuti aturan Tenet 14:
- Dilarang membungkus error dengan `except Exception: pass` atau mengembalikan nilai dummy palsu (`return True`, `return 0`, `Ok(())`) tanpa eksekusi nyata.
- Apabila suatu fungsionalitas belum diimplementasikan atau dependensi belum tersedia, kode wajib melempar eksepsi bertipe eksplisit (`raise NotImplementedError(...)`) agar agen atau developer segera menyadari kegagalan tersebut.
