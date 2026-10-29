# 12. Glosarium dan Istilah (Glossary)

> [!INFO] **Architecture Provenance & Freshness**
> - **Verified Commit**: `b81c7a3` (branch: `main`)
> - **Verified Timestamp**: `2026-10-29T14:04:00+07:00`
> - **Tracked Paths**: `skills/`, `config/`, `install.sh`
> - **Drift Status**: `verified`

Dokumen ini memuat definisi istilah teknis, singkatan, dan konsep arsitektur yang digunakan dalam ekosistem `agent-skills`.

---

## 12.1 Istilah Arsitektur & Rekayasa Perangkat Lunak

| Istilah | Definisi Singkat |
|:---|:---|
| **ADR (Architectural Decision Record)** | Dokumen terstruktur berformat teks yang mencatat keputusan arsitektur penting bersama konteks dan konsekuensinya. |
| **arc42** | Standar internasional berbasis templat terbuka (selaras dengan ISO/IEC/IEEE 42010) untuk menyusun dokumentasi arsitektur sistem secara modular dan berorientasi pragmatis. |
| **Architecture Drift** | Fenomena degradasi atau pergeseran ketika kode sumber aktual terus berkembang tetapi dokumentasi arsitekturnya tertinggal dan usang. |
| **AST (Abstract Syntax Tree)** | Struktur pohon hierarkis yang merepresentasikan tata bahasa dan struktur sintaksis dari kode program komputer yang dihasilkan oleh parser. |
| **Blast Radius** | Cakupan atau luas area risiko regresi pada modul-modul lain ketika sebuah fungsi, kelas, atau antarmuka diubah. |
| **CVSS (Common Vulnerability Scoring System)** | Standar industri terbuka untuk menilai tingkat keparahan celah keamanan kerentanan perangkat lunak (skor 0.0 hingga 10.0). |
| **Dual-Tier Verification** | Pola pemisahan antara aturan ketat invarian statis global (alat tanpa kompromi) dengan buku besar hutang teknis repositori yang terdokumentasi formal. |
| **Evidence-First ("Old Coder")** | Filosofi rekayasa yang menegaskan: *"Review evidence, not code"*. Menyatakan suatu fitur atau perbaikan selesai hanya jika disertai bukti log terminal dan pengujian riil. |
| **OSV (Open Source Vulnerability)** | Format skema terbuka berbasis JSON yang distandarisasi untuk mengagregasi data keamanan celah pustaka open-source lintas ekosistem. |
| **OSV-SCALIBR** | Pustaka inti ekstraksi dependensi berbasis Go yang dikembangkan Google untuk Software Composition Analysis (SCA) dan remediasi. |
| **Q42 Quality Model** | Taksonomi evaluasi mutu arsitektur perangkat lunak yang mengklasifikasikan sasaran dan skenario mutu ke dalam tag keterlacakan (misal: `#correctness`, `#performance`, `#security`). |
| **REPR (Request-Endpoint-Response)** | Pola desain berorientasi irisan vertikal yang mengelompokkan request, endpoint, dan response dalam satu unit fitur tunggal tanpa pemisahan horizontal bertingkat. |
| **SOLID** | Lima prinsip desain berorientasi objek: Single Responsibility, Open-Closed, Liskov Substitution, Interface Segregation, dan Dependency Inversion. |
| **SRP (Single Responsibility Principle)** | Prinsip yang menyatakan bahwa setiap modul, fungsi, atau kelas hanya boleh memiliki satu alasan untuk berubah. |
| **VSA (Vertical Slice Architecture)** | Pendekatan arsitektur perangkat lunak yang mengorganisasi kode berdasarkan kapabilitas bisnis atau fitur vertikal, bukan lapisan teknis horizontal. |
| **Zero-Mock Policy** | Kebijakan ketat yang melarang keberadaan kode mock, dummy stub palsu, atau simulator latensi tiruan di jalur eksekusi produksi. |
