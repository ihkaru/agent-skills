# 7. Tampilan Penyebaran (Deployment View)

> [!INFO] **Architecture Provenance & Freshness**
> - **Verified Commit**: `606a98b` (branch: `main`)
> - **Verified Timestamp**: `2026-10-29T13:30:00+07:00`
> - **Tracked Paths**: `skills/`, `config/`, `install.sh`
> - **Drift Status**: `verified`

Dokumen ini menjelaskan topologi fisik dan infrastruktur lingkungan tempat seluruh komponen repositori `agent-skills` disebarkan dan dieksekusi.

---

## 7.1 Topologi Penyebaran Infrastruktur

```mermaid
graph TD
    subgraph DeveloperWorkstation ["Developer Workstation / CI Runner"]
        subgraph UserHome ["$HOME Directory"]
            subgraph GeminiConfig ["~/.gemini/config/"]
                GEMINI_MD["GEMINI.md (Global Standing Rules)"]
                SKILLS_JSON["skills.json (Skills Registry)"]
                subgraph SymlinkedSkills ["~/.gemini/config/skills/"]
                    SKILL_CRAFTSMAN["craftsman-coder -> repo"]
                    SKILL_ARC42["arc42-architect -> repo"]
                    SKILL_ZEROMOCK["zero-mock-detector -> repo"]
                    SKILL_OSV["osv-scanner -> repo"]
                    SKILL_COOLIFY["thinkstation-coolify -> repo"]
                end
            end
            
            subgraph LocalBin ["~/.local/bin/ (In PATH)"]
                BIN_OSV_GATE["osv-scanner-gate / osv-gate"]
                BIN_OSV_SCANNER["osv-scanner (Google Go Binary)"]
                BIN_ARC42["arc42-lint / arc42-pre-commit"]
                BIN_MOCKS["detect-mocks / zero-mock-detector"]
                BIN_COOLIFY["coolify-control"]
                BIN_SRP["static-srp-analyzer"]
                BIN_IMPACT["codegraph-impact"]
                BIN_VSA["vsa-boundary-checker"]
            end
        end
    end

    subgraph ExternalCloud ["Cloud & Remote Servers"]
        OSV_API["Google OSV.dev (api.osv.dev)"]
        INFISICAL_VAULT["Infisical Secret Vault (secrets.dvlpid.my.id)"]
        COOLIFY_SERVER["ThinkStation Server (100.101.49.42 / LAN)"]
    end

    BIN_OSV_GATE --> OSV_API
    BIN_COOLIFY --> INFISICAL_VAULT
    BIN_COOLIFY --> COOLIFY_SERVER
```

---

## 7.2 Pemetaan Komponen ke Node Infrastruktur

Berikut adalah pemetaan penyebaran setiap blok pembangun Level 1 ke dalam sistem file lokal dan lingkungan eksekusi:

1. **Craftsman Coder Core**:
   - **Lokasi Fisik**: Disimpan di `skills/craftsman-coder/` dan disymlink ke `~/.gemini/config/skills/craftsman-coder`.
   - **Kakas Eksekusi**: Biner perintah mandiri ditautkan ke `~/.local/bin/static-srp-analyzer`, `~/.local/bin/codegraph-impact`, dan `~/.local/bin/vsa-boundary-checker`.
   - **Runtime**: Python 3.9+ Standard Library tanpa dependensi eksternal.

2. **arc42 Architecture Engine**:
   - **Lokasi Fisik**: Disimpan di `skills/arc42-architect/` dan disymlink ke `~/.gemini/config/skills/arc42-architect`.
   - **Kakas Eksekusi**: Ditautkan ke `~/.local/bin/arc42-lint` dan `~/.local/bin/arc42-pre-commit`.
   - **Kamus Bahasa**: Membaca file terjemahan JSON dari `skills/arc42-architect/scripts/languages/`.

3. **Zero-Mock Static Detector**:
   - **Lokasi Fisik**: Disimpan di `skills/zero-mock-detector/` dan disymlink ke `~/.gemini/config/skills/zero-mock-detector`.
   - **Kakas Eksekusi**: Ditautkan ke `~/.local/bin/detect-mocks` dan `~/.local/bin/zero-mock-detector` (serta `/usr/local/bin/` jika root).
   - **Runtime**: AST inspector mandiri Python standard library.

4. **OSV-Scanner Security Gate**:
   - **Lokasi Fisik**: Disimpan di `skills/osv-scanner/` dan disymlink ke `~/.gemini/config/skills/osv-scanner`.
   - **Kakas Eksekusi**: Ditautkan ke `~/.local/bin/osv-scanner-gate` dan `~/.local/bin/osv-gate`.
   - **Biner Pendukung**: Memanggil biner Go Google `osv-scanner` yang terpasang di `/usr/bin/osv-scanner` atau `~/.local/bin/osv-scanner`.
   - **Konektivitas Jaringan**: Menghubungi `https://api.osv.dev` melalui kueri batch HTTPS/2.

5. **ThinkStation Coolify CLI**:
   - **Lokasi Fisik**: Disimpan di `skills/thinkstation-coolify/` dan disymlink ke `~/.gemini/config/skills/thinkstation-coolify`.
   - **Kakas Eksekusi**: Ditautkan ke `~/.local/bin/coolify-control`.
   - **Konektivitas Jaringan**: Menghubungi Infisical Vault via HTTPS dan ThinkStation Coolify Server via WireGuard Tailscale Mesh (`100.101.49.42`) atau LAN IP (`192.168.0.136`).
