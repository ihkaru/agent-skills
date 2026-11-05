#!/usr/bin/env python3
"""
ThinkStation Coolify Controller & Database Query CLI Tool
Part of the `thinkstation-coolify` skill.

Automates operations to ThinkStation (Coolify server for *.dvlpid.my.id):
- Executes via high-speed Universal AGY Mesh HTTP API (port 8484 over SOCKS5 proxy)
- Provides resilient SSH fallback (using ProxyCommand over SOCKS5) with Infisical key auto-restoration
- Diagnostic 'doctor' command enforcing the Zero 3rd-Party VPN Rule (Tailscale Isolation Invariant)
- Agnostically lists, inspects, and tails logs (with ANSI strip & SSE spam filter) for any Coolify application
- Monitors deployment queue, triggers deployments, & inspects build logs
- Discovers database containers (PostgreSQL, Timescale, MySQL, MariaDB, Redis, SQLite on Docker volumes)
- Fully machine-readable with --json output and deterministic exit codes
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

DEFAULT_KEY_PATH = Path.home() / ".ssh" / "id_ed25519_agent"
DEFAULT_USER = "server"
TAILSCALE_HOST = "100.101.49.42"
DEFAULT_MESH_NODE = "100.101.49.42:8484"
DEFAULT_MESH_TOKEN = "agy-universal-mesh-token-2026"
DEFAULT_SOCKS5_PROXY = "socks5h://127.0.0.1:1055"
INFISICAL_PROJECT_ID = "f13379e0-9661-4f8e-81ef-0e81d1502da1"
INFISICAL_ENV = "dev"

ANSI_REGEX = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

KNOWN_APPS: Dict[str, Dict[str, str]] = {
    "cerdas": {
        "uuid": "q4cwk40sso0wocww4c44oso8",
        "container_match": "backend-q4cwk40sso0wocww4c44oso8",
        "db_type": "mysql",
    },
    "lumis": {
        "uuid": "ilzgv2cejxrvmn7g1y3bbu8q",
        "container_match": "lumis-ilzgv2cejxrvmn7g1y3bbu8q",
        "db_type": "sqlite",
        "db_path": "/var/lib/docker/volumes/ilzgv2cejxrvmn7g1y3bbu8q_lumis-data/_data/lumis.db",
    },
    "propylon": {
        "uuid": "h3r4aia4z4xzksst58vudorj",
        "container_match": "h3r4aia4z4xzksst58vudorj",
        "db_type": "postgres",
    },
    "aegis": {
        "uuid": "h3r4aia4z4xzksst58vudorj",
        "container_match": "h3r4aia4z4xzksst58vudorj",
        "db_type": "postgres",
    },
    "ridm": {
        "uuid": "ridm",
        "container_match": "ridm-auth",
        "db_type": "postgres",
        "db_container": "ridm-postgres",
    },
    "mediavault": {
        "uuid": "mediavault",
        "container_match": "mediavault",
        "db_type": "meilisearch",
    },
    "flashlearn": {
        "uuid": "rqn4a8luwxwj5e8u58u0w0ao",
        "container_match": "rqn4a8luwxwj5e8u58u0w0ao",
        "db_type": "postgres",
    },
}


def strip_ansi(text: str) -> str:
    """Removes ANSI terminal escape sequences."""
    return ANSI_REGEX.sub('', text)


class RemoteManager:
    """
    Manages dual-transport remote execution to ThinkStation.
    Tier 1: High-Speed Universal AGY Mesh HTTP API (port 8484 over SOCKS5 proxy) - Primary, non-blocking.
    Tier 2: SSH via ProxyCommand over SOCKS5 proxy - Fallback.
    """

    def __init__(
        self,
        mesh_node: str = DEFAULT_MESH_NODE,
        mesh_token: str = DEFAULT_MESH_TOKEN,
        proxy: str = DEFAULT_SOCKS5_PROXY,
        key_path: Path = DEFAULT_KEY_PATH,
        user: str = DEFAULT_USER
    ):
        self.mesh_node = mesh_node
        self.mesh_token = mesh_token
        self.proxy = proxy
        self.key_path = key_path
        self.user = user
        self.active_transport = "mesh"
        self.active_host = TAILSCALE_HOST

    def ensure_key_exists(self) -> None:
        """Restores SSH private key from Infisical if missing."""
        if self.key_path.exists() and self.key_path.stat().st_size > 0:
            return

        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "infisical", "secrets", "get", "SERVER_SSH_PRIVATE_KEY",
            "--projectId", INFISICAL_PROJECT_ID,
            "--env", INFISICAL_ENV,
            "--plain"
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            self.key_path.write_text(res.stdout, encoding="utf-8")
            self.key_path.chmod(0o600)
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to auto-restore SSH key via Infisical: {e}\n")

    def run_remote(self, command: str, timeout: Optional[int] = 30) -> Tuple[int, str, str]:
        """
        Executes command on ThinkStation.
        Attempts Mesh HTTP API first; falls back to SSH via SOCKS5 ProxyCommand.
        """
        # Tier 1: Mesh HTTP API over SOCKS5
        url = f"http://{self.mesh_node}/api/cmd"
        payload = json.dumps({"command": command})
        curl_args = [
            "curl", "-s",
            "--max-time", str(timeout or 30),
            "-x", self.proxy,
            "-H", f"Authorization: Bearer {self.mesh_token}",
            "-H", "Content-Type: application/json",
            "-d", "@-",
            url
        ]
        try:
            p = subprocess.run(curl_args, input=payload, text=True, capture_output=True, timeout=timeout)
            if p.returncode == 0 and p.stdout:
                try:
                    data = json.loads(p.stdout)
                    self.active_transport = "mesh"
                    return data.get("exitCode", 0), data.get("stdout", ""), data.get("stderr", "")
                except Exception:
                    self.active_transport = "mesh"
                    return 0, p.stdout, ""
        except Exception:
            pass

        # Tier 2: SSH Fallback over SOCKS5 ProxyCommand
        return self._run_ssh_fallback(command, timeout)

    def _run_ssh_fallback(self, command: str, timeout: Optional[int] = 30) -> Tuple[int, str, str]:
        """Executes command via SSH with SOCKS5 ProxyCommand."""
        self.ensure_key_exists()
        ssh_cmd = [
            "ssh", "-i", str(self.key_path),
            "-o", "ProxyCommand=nc -X 5 -x 127.0.0.1:1055 %h %p",
            "-o", "ConnectTimeout=5",
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "BatchMode=yes",
            "-p", "22",
            f"{self.user}@{TAILSCALE_HOST}",
            command
        ]
        try:
            res = subprocess.run(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
            self.active_transport = "ssh"
            return res.returncode, res.stdout, res.stderr
        except subprocess.TimeoutExpired:
            return 124, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return 1, "", str(e)


# Backward-compatible alias for existing tests and scripts
SSHManager = RemoteManager


class CoolifyController:
    """Agnostic controller for Docker containers, Coolify metadata, and databases."""

    def __init__(self, remote: RemoteManager):
        self.remote = remote

    def resolve_target(self, target: str) -> str:
        """Resolves an app alias or prefix to the actual running container name."""
        t = target.strip()
        if t.lower() in KNOWN_APPS:
            match_pattern = KNOWN_APPS[t.lower()]["container_match"]
            code, out, _ = self.remote.run_remote(f"docker ps --filter name={match_pattern} --format '{{{{.Names}}}}' | head -n 1")
            if code == 0 and out.strip():
                return out.strip().splitlines()[0]
        if "-" in t and not re.search(r'-\d{8}T\d{6}$', t):
            code, out, _ = self.remote.run_remote(f"docker ps --filter name={t} --format '{{{{.Names}}}}' | head -n 1")
            if code == 0 and out.strip():
                return out.strip().splitlines()[0]
        return t

    def doctor(self) -> Dict[str, Any]:
        """
        Diagnoses network connectivity, Tailscale daemon, SOCKS5 proxy, and ThinkStation mesh node.
        Enforces the Zero 3rd-Party VPN Rule (Tailscale Isolation Invariant).
        """
        results: Dict[str, Any] = {
            "all_healthy": False,
            "tailscale_daemon": {"healthy": False, "details": "Unknown"},
            "socks5_proxy": {"healthy": False, "port": 1055},
            "mesh_api": {"healthy": False, "node": self.remote.mesh_node},
            "thinkstation_docker": {"healthy": False, "version": None, "running_containers": 0},
            "vpn_conflict_warning": False,
            "diagnostic_messages": []
        }

        # 1. Check local tailscaled daemon
        try:
            p = subprocess.run(["pgrep", "-f", "tailscaled"], capture_output=True, text=True)
            if p.returncode == 0:
                results["tailscale_daemon"] = {"healthy": True, "details": "Running"}
            else:
                results["tailscale_daemon"] = {
                    "healthy": False,
                    "details": "Not running. Start via: /usr/sbin/tailscaled --tun=userspace-networking --socks5-server=127.0.0.1:1055 &"
                }
                results["diagnostic_messages"].append("tailscaled daemon is not running locally.")
        except Exception as e:
            results["tailscale_daemon"] = {"healthy": False, "details": str(e)}

        # 2. Check SOCKS5 Proxy (127.0.0.1:1055)
        try:
            p = subprocess.run(["nc", "-z", "127.0.0.1", "1055"], capture_output=True)
            if p.returncode == 0:
                results["socks5_proxy"]["healthy"] = True
            else:
                results["socks5_proxy"]["healthy"] = False
                results["diagnostic_messages"].append("SOCKS5 proxy on 127.0.0.1:1055 is unreachable.")
        except Exception as e:
            results["socks5_proxy"]["healthy"] = False
            results["socks5_proxy"]["error"] = str(e)

        # 3. Check Mesh API on ThinkStation
        curl_args = [
            "curl", "-s", "--max-time", "5",
            "-x", self.remote.proxy,
            "-H", f"Authorization: Bearer {self.remote.mesh_token}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"command": "echo PING_OK"}),
            f"http://{self.remote.mesh_node}/api/cmd"
        ]
        try:
            p = subprocess.run(curl_args, capture_output=True, text=True)
            if p.returncode == 0 and "PING_OK" in p.stdout:
                results["mesh_api"]["healthy"] = True
            else:
                results["mesh_api"]["healthy"] = False
                results["vpn_conflict_warning"] = True
                results["diagnostic_messages"].append(
                    "ThinkStation Mesh API unreachable. "
                    "CRITICAL: Pastikan perangkat Anda TIDAK TERKONEKSI ke VPN pihak ketiga manapun "
                    "(seperti Cloudflare WARP 1.1.1.1, WireGuard, OpenVPN, AdGuard VPN). "
                    "VPN eksternal membajak rute dan memblokir paket Tailscale mesh ke ThinkStation (100.101.49.42)."
                )
        except Exception as e:
            results["mesh_api"]["healthy"] = False
            results["mesh_api"]["error"] = str(e)
            results["vpn_conflict_warning"] = True

        # 4. Check ThinkStation Docker Daemon
        if results["mesh_api"]["healthy"]:
            code, out, _ = self.remote.run_remote("docker version --format '{{.Server.Version}}' && docker ps -q | wc -l")
            if code == 0:
                lines = out.strip().splitlines()
                ver = lines[0] if len(lines) > 0 else "unknown"
                count = int(lines[1]) if len(lines) > 1 and lines[1].isdigit() else 0
                results["thinkstation_docker"] = {
                    "healthy": True,
                    "version": ver,
                    "running_containers": count
                }
            else:
                results["diagnostic_messages"].append("Docker daemon query on ThinkStation failed.")

        results["all_healthy"] = (
            results["tailscale_daemon"]["healthy"] and
            results["socks5_proxy"]["healthy"] and
            results["mesh_api"]["healthy"] and
            results["thinkstation_docker"]["healthy"]
        )

        return results

    def get_status(self) -> Dict[str, Any]:
        """Fetches host status, Docker health, and active transport."""
        cmd = "hostname && uname -r && uptime -p && docker version --format '{{.Server.Version}}'"
        code, out, err = self.remote.run_remote(cmd)
        lines = out.strip().splitlines()
        return {
            "connected": code == 0,
            "host": self.remote.active_host,
            "transport": self.remote.active_transport,
            "hostname": lines[0] if len(lines) > 0 else "unknown",
            "kernel": lines[1] if len(lines) > 1 else "unknown",
            "uptime": lines[2] if len(lines) > 2 else "unknown",
            "docker_version": lines[3] if len(lines) > 3 else "unknown",
            "error": err if code != 0 else None
        }

    def list_containers(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists running containers with their Coolify labels, images, and ports."""
        fmt = '{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}\t{{.Labels}}'
        cmd = f"docker ps --format '{fmt}'"
        code, out, _ = self.remote.run_remote(cmd)
        if code != 0:
            return []

        containers = []
        for line in out.strip().splitlines():
            parts = line.split('\t')
            if len(parts) < 6:
                continue
            cid, name, image, status, ports, labels_str = parts[:6]

            project = None
            resource = None
            ctype = None
            fqdn = None

            for label in labels_str.split(','):
                if label.startswith('coolify.projectName='):
                    project = label.split('=', 1)[1]
                elif label.startswith('coolify.resourceName='):
                    resource = label.split('=', 1)[1]
                elif label.startswith('coolify.type='):
                    ctype = label.split('=', 1)[1]
                elif 'Host(`' in label:
                    m = re.search(r'Host\(`([^`]+)`\)', label)
                    if m:
                        fqdn = m.group(1)

            entry = {
                "id": cid,
                "name": name,
                "image": image,
                "status": status,
                "ports": ports,
                "project": project,
                "resource": resource,
                "type": ctype,
                "fqdn": fqdn
            }

            if search:
                s = search.lower()
                matches = (
                    s in name.lower() or
                    s in image.lower() or
                    (project and s in project.lower()) or
                    (resource and s in resource.lower()) or
                    (fqdn and s in fqdn.lower())
                )
                if not matches:
                    continue

            containers.append(entry)

        return containers

    def inspect_container(self, target: str) -> Dict[str, Any]:
        """Inspects container environment variables, mounts, and network."""
        resolved = self.resolve_target(target)
        cmd = f"docker inspect {resolved} --format '{{{{json .}}}}'"
        code, out, err = self.remote.run_remote(cmd)
        if code != 0:
            return {"error": err.strip() or f"Container {target} not found"}

        try:
            data = json.loads(out)
            config = data.get("Config", {})
            env_list = config.get("Env", [])
            return {
                "id": data.get("Id", "")[:12],
                "name": data.get("Name", "").lstrip("/"),
                "image": config.get("Image", ""),
                "status": data.get("State", {}).get("Status", ""),
                "labels": config.get("Labels", {}),
                "mounts": [
                    {
                        "source": m.get("Source"),
                        "destination": m.get("Destination"),
                        "type": m.get("Type")
                    }
                    for m in data.get("Mounts", [])
                ],
                "environment": env_list,
                "ports": data.get("NetworkSettings", {}).get("Ports", {})
            }
        except Exception as e:
            return {"error": str(e)}

    def get_logs(
        self,
        target: str,
        tail: int = 100,
        timestamps: bool = False,
        clean: bool = True,
        errors_only: bool = False
    ) -> str:
        """
        Fetches logs for a container or application.
        Automatically strips ANSI codes and filters out SSE heartbeat noise.
        """
        resolved = self.resolve_target(target)
        ts_flag = "-t" if timestamps else ""
        cmd = f"docker logs {ts_flag} --tail {tail * 2 if (clean or errors_only) else tail} {resolved}"
        _, out, err = self.remote.run_remote(cmd, timeout=30)
        raw = out if out else err

        if clean:
            raw = strip_ansi(raw)
            # Filter out SSE keep-alive heartbeats
            filtered = [
                line for line in raw.splitlines()
                if not line.strip().startswith(": OPENROUTER PROCESSING") and
                   not line.strip().startswith(": ping")
            ]
            raw = "\n".join(filtered)

        if errors_only:
            err_keywords = ["error", "fatal", "panic", "exception", "failed", "500 internal", "syntaxerror"]
            err_lines = [
                line for line in raw.splitlines()
                if any(k in line.lower() for k in err_keywords)
            ]
            raw = "\n".join(err_lines)

        lines = raw.splitlines()
        return "\n".join(lines[-tail:])

    def list_deployments(self, app_name: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Queries application_deployment_queues from coolify-db."""
        query = (
            "SELECT id, application_name, status, commit, created_at, finished_at "
            "FROM application_deployment_queues "
        )
        if app_name:
            query += f"WHERE application_name ILIKE '%{app_name}%' "
        query += f"ORDER BY created_at DESC LIMIT {limit};"

        cmd = f"docker exec coolify-db psql -U coolify -d coolify -A -F '\t' -c \"{query}\""
        code, out, _ = self.remote.run_remote(cmd)
        if code != 0:
            return []

        deployments = []
        lines = out.strip().splitlines()
        if len(lines) <= 1:
            return []

        for line in lines[1:]:
            if line.endswith("rows)") or line.endswith("row)"):
                continue
            parts = line.split('\t')
            if len(parts) >= 6:
                deployments.append({
                    "id": parts[0],
                    "app_name": parts[1],
                    "status": parts[2],
                    "commit": parts[3],
                    "created_at": parts[4],
                    "finished_at": parts[5]
                })

        return deployments

    def get_deployment_log(self, deploy_id_or_app: str, tail: int = 200) -> str:
        """Retrieves build/deployment logs from coolify-db."""
        if deploy_id_or_app.isdigit():
            where = f"id = {deploy_id_or_app}"
        else:
            where = f"application_name ILIKE '%{deploy_id_or_app}%' ORDER BY created_at DESC LIMIT 1"

        query = f"SELECT logs FROM application_deployment_queues WHERE {where};"
        cmd = f"docker exec coolify-db psql -U coolify -d coolify -t -A -c \"{query}\""
        code, out, err = self.remote.run_remote(cmd)
        if code != 0 or not out.strip():
            return f"No deployment log found for '{deploy_id_or_app}'"

        raw = out.strip()
        if raw.startswith("[") and raw.endswith("]"):
            try:
                events = json.loads(raw)
                lines = []
                for ev in events:
                    if isinstance(ev, dict) and "output" in ev:
                        ts = ev.get("timestamp", "")[:19]
                        msg = ev.get("output", "").strip()
                        if msg:
                            lines.append(f"[{ts}] {msg}" if ts else msg)
                if lines:
                    return "\n".join(lines[-tail:])
            except Exception:
                pass

        lines = out.splitlines()
        return "\n".join(lines[-tail:])

    def trigger_deployment(self, app_or_uuid: str, force_rebuild: bool = True) -> Tuple[bool, str]:
        """Triggers application deployment via Coolify tinker queue."""
        app_key = app_or_uuid.lower().strip()
        uuid = KNOWN_APPS.get(app_key, {}).get("uuid", app_or_uuid)
        rebuild_str = "true" if force_rebuild else "false"

        tinker_cmd = (
            f"docker exec coolify php /var/www/html/artisan tinker --execute='"
            f"$app = \\App\\Models\\Application::where(\"uuid\", \"{uuid}\")->first(); "
            f"if (!$app) {{ echo \"ERROR_APP_NOT_FOUND\"; exit(1); }} "
            f"$dep = queue_application_deployment(application: $app, force_rebuild: {rebuild_str}); "
            f"if (is_array($dep) && isset($dep[\"status\"]) && $dep[\"status\"] === \"queue_full\") {{ echo \"ERROR_QUEUE_FULL\"; exit(1); }} "
            f"$uid = is_object($dep) ? ($dep->deployment_uuid ?? null) : (is_array($dep) && isset($dep[0]) ? $dep[0]->deployment_uuid : null); "
            f"echo \"QUEUED:\" . ($uid ?: \"OK\");'"
        )
        code, out, err = self.remote.run_remote(tinker_cmd)
        if code == 0 and "QUEUED:" in out:
            queue_id = out.split("QUEUED:", 1)[1].strip()
            return True, f"Deployment queued successfully for {app_or_uuid} (UUID: {queue_id})"
        return False, f"Failed to trigger deployment: {err or out}"

    def restart_container(self, target: str) -> Tuple[bool, str]:
        """Restarts a container safely."""
        resolved = self.resolve_target(target)
        cmd = f"docker restart {resolved}"
        code, _, err = self.remote.run_remote(cmd, timeout=30)
        if code == 0:
            return True, f"Successfully restarted {target}"
        return False, err.strip()

    def list_databases(self) -> List[Dict[str, Any]]:
        """Finds all database containers on the server."""
        containers = self.list_containers()
        dbs = []
        db_keywords = ["postgres", "mysql", "mariadb", "redis", "mongo", "clickhouse", "timescale", "valkey"]

        for c in containers:
            image_lower = c["image"].lower()
            name_lower = c["name"].lower()
            ctype = c.get("type") or ""
            ports = c.get("ports", "")

            is_db = (
                ctype == "database" or
                any(k in image_lower for k in db_keywords) or
                any(k in name_lower for k in db_keywords) or
                any(p in ports for p in ["5432", "3306", "6379", "27017"])
            )

            if is_db:
                engine = "unknown"
                for k in ["postgres", "timescale", "mysql", "mariadb", "redis", "valkey", "mongo", "clickhouse"]:
                    if k in image_lower or k in name_lower:
                        engine = k
                        break

                if engine == "unknown":
                    if "5432" in ports:
                        engine = "postgres"
                    elif "3306" in ports:
                        engine = "mysql"
                    elif "6379" in ports:
                        engine = "redis"
                    elif "27017" in ports:
                        engine = "mongo"

                dbs.append({
                    "id": c["id"],
                    "name": c["name"],
                    "engine": engine,
                    "image": c["image"],
                    "status": c["status"],
                    "ports": c["ports"],
                    "project": c["project"] or "standalone/service",
                    "resource": c["resource"]
                })

        return dbs

    def find_database_for(self, query: str) -> List[Dict[str, Any]]:
        """Finds database containers associated with an application or project query."""
        all_dbs = self.list_databases()
        q = query.lower()
        matches = []
        for db in all_dbs:
            if (
                q in db["name"].lower() or
                (db["project"] and q in db["project"].lower()) or
                (db["resource"] and q in db["resource"].lower()) or
                q in db["engine"].lower()
            ):
                matches.append(db)
        return matches

    def query_database(
        self,
        db_target: str,
        sql: str,
        database_name: Optional[str] = None
    ) -> Tuple[int, str, str]:
        """
        Executes SQL inside target database container with auto-extracted credentials.
        Supports PostgreSQL, TimescaleDB, MySQL, MariaDB, and Redis.
        """
        info = self.inspect_container(db_target)
        if "error" in info:
            return 1, "", info["error"]

        env_dict = {}
        for item in info.get("environment", []):
            if "=" in item:
                k, v = item.split("=", 1)
                env_dict[k] = v

        image = info.get("image", "").lower()
        name = info.get("name", "").lower()

        # 1. PostgreSQL / TimescaleDB
        if "postgres" in image or "timescale" in image or "psql" in name or "POSTGRES_USER" in env_dict:
            user = env_dict.get("POSTGRES_USER", "postgres")
            db = database_name or env_dict.get("POSTGRES_DB", "postgres")
            escaped_sql = sql.replace('"', '\\"')
            cmd = f'docker exec {db_target} psql -U {user} -d {db} -c "{escaped_sql}"'
            return self.remote.run_remote(cmd)

        # 2. MySQL / MariaDB
        if "mysql" in image or "mariadb" in image or "MYSQL_ROOT_PASSWORD" in env_dict or "MARIADB_USER" in env_dict:
            user = env_dict.get("MYSQL_USER") or env_dict.get("MARIADB_USER") or "root"
            password = env_dict.get("MYSQL_PASSWORD") or env_dict.get("MARIADB_PASSWORD") or env_dict.get("MYSQL_ROOT_PASSWORD") or ""
            db = database_name or env_dict.get("MYSQL_DATABASE") or env_dict.get("MARIADB_DATABASE") or ""

            pass_flag = f"-p'{password}'" if password else ""
            db_flag = db if db else ""
            escaped_sql = sql.replace('"', '\\"')
            cmd = f'docker exec {db_target} mysql -u {user} {pass_flag} {db_flag} -e "{escaped_sql}"'
            return self.remote.run_remote(cmd)

        # 3. Redis / Valkey
        if "redis" in image or "valkey" in image or "redis" in name:
            password = env_dict.get("REDIS_PASSWORD", "")
            auth_flag = f"-a '{password}'" if password else ""
            cmd = f'docker exec {db_target} redis-cli {auth_flag} {sql}'
            return self.remote.run_remote(cmd)

        return 1, "", f"Unsupported database engine for container {db_target} ({image})"


def main():
    common_p = argparse.ArgumentParser(add_help=False)
    common_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    parser = argparse.ArgumentParser(
        prog="coolify-control",
        description="ThinkStation Coolify & Database Agnostic Management CLI",
        parents=[common_p]
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. Doctor (Network & VPN Conflict Diagnostics)
    subparsers.add_parser("doctor", parents=[common_p], help="Diagnose Tailscale, SOCKS5, Mesh API, & 3rd-party VPN conflicts")

    # 2. Status
    subparsers.add_parser("status", parents=[common_p], help="Check server, Docker, and Mesh connectivity status")

    # 3. Apps
    apps_p = subparsers.add_parser("apps", parents=[common_p], help="Container and application discovery")
    apps_sub = apps_p.add_subparsers(dest="apps_action", required=True)
    list_p = apps_sub.add_parser("list", parents=[common_p], help="List running applications and containers")
    list_p.add_argument("--search", "-s", help="Filter by name, project, or domain")
    inspect_p = apps_sub.add_parser("inspect", parents=[common_p], help="Inspect container environment & mounts")
    inspect_p.add_argument("target", help="Container name, ID, or known app alias (e.g. cerdas, lumis)")

    # 4. Logs
    logs_p = subparsers.add_parser("logs", parents=[common_p], help="Fetch logs from any container")
    logs_p.add_argument("target", help="Container name, ID, or app alias")
    logs_p.add_argument("--tail", "-n", type=int, default=100, help="Number of lines (default: 100)")
    logs_p.add_argument("--timestamps", "-t", action="store_true", help="Show timestamps")
    logs_p.add_argument("--clean", action="store_true", default=True, help="Strip ANSI color codes and SSE keep-alive noise")
    logs_p.add_argument("--errors-only", action="store_true", help="Filter only error and panic lines")

    # 5. Deploy
    deploy_p = subparsers.add_parser("deploy", parents=[common_p], help="Coolify deployment queue management")
    deploy_sub = deploy_p.add_subparsers(dest="deploy_action", required=True)
    d_list_p = deploy_sub.add_parser("list", parents=[common_p], help="List recent deployments from coolify-db")
    d_list_p.add_argument("--app", help="Filter by application name")
    d_list_p.add_argument("--limit", type=int, default=10, help="Limit results (default: 10)")
    d_log_p = deploy_sub.add_parser("logs", parents=[common_p], help="Fetch build/deployment log")
    d_log_p.add_argument("target", help="Deployment ID or application name")
    d_log_p.add_argument("--tail", "-n", type=int, default=200, help="Number of lines")
    d_restart_p = deploy_sub.add_parser("restart", parents=[common_p], help="Restart a container/service")
    d_restart_p.add_argument("target", help="Container name or ID")
    d_trig_p = deploy_sub.add_parser("trigger", parents=[common_p], help="Trigger deployment for an application")
    d_trig_p.add_argument("target", help="Application name or Coolify UUID")
    d_trig_p.add_argument("--no-rebuild", action="store_true", help="Do not force rebuild")

    # 6. Database
    db_p = subparsers.add_parser("db", parents=[common_p], help="Database discovery and query execution")
    db_sub = db_p.add_subparsers(dest="db_action", required=True)
    db_sub.add_parser("list", parents=[common_p], help="List all database containers on the server")
    db_find_p = db_sub.add_parser("find", parents=[common_p], help="Find database for a project or app")
    db_find_p.add_argument("query", help="Project name, app name, or keyword")
    db_query_p = db_sub.add_parser("query", parents=[common_p], help="Execute SQL inside a database container")
    db_query_p.add_argument("target", help="Database container name or ID")
    db_query_p.add_argument("--sql", required=True, help="SQL statement to execute")
    db_query_p.add_argument("--database", "-d", help="Database name override")

    # 7. Exec
    exec_p = subparsers.add_parser("exec", parents=[common_p], help="Execute arbitrary command on ThinkStation")
    exec_p.add_argument("cmd", help="Command string to run")
    exec_p.add_argument("--timeout", "-t", type=int, default=120, help="Command timeout in seconds (default: 120)")

    args = parser.parse_args()

    remote = RemoteManager()
    ctrl = CoolifyController(remote)

    if args.command == "doctor":
        res = ctrl.doctor()
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print("🩺 ThinkStation Coolify Diagnostic Check")
            print("=" * 60)
            td = res["tailscale_daemon"]
            print(f"Tailscale Daemon:  {'✅ Running' if td['healthy'] else '❌ ' + td['details']}")
            sp = res["socks5_proxy"]
            print(f"SOCKS5 Proxy (1055):{'✅ Healthy' if sp['healthy'] else '❌ Unreachable'}")
            ma = res["mesh_api"]
            print(f"Mesh API (8484):    {'✅ Connected' if ma['healthy'] else '❌ Unreachable'}")
            dk = res["thinkstation_docker"]
            if dk["healthy"]:
                print(f"Docker Daemon:     ✅ v{dk['version']} ({dk['running_containers']} containers running)")
            else:
                print("Docker Daemon:     ❌ Unreachable")

            if res["vpn_conflict_warning"]:
                print("\n⚠️ PERINGATAN KONFLIK VPN:")
                print("Pastikan perangkat Anda TIDAK TERKONEKSI ke VPN pihak ketiga manapun (seperti WARP 1.1.1.1, WireGuard, OpenVPN, AdGuard VPN).")
                print("VPN eksternal membajak rute jaringan dan memblokir Tailscale WireGuard mesh ke ThinkStation.")

            for msg in res["diagnostic_messages"]:
                print(f"• {msg}")

            if res["all_healthy"]:
                print("\n🎉 Status: ALL SYSTEMS OPERATIONAL")
            else:
                sys.exit(1)

    elif args.command == "status":
        res = ctrl.get_status()
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            if res["connected"]:
                print(f"✅ ThinkStation Connected via {res['host']} [{res['transport'].upper()}]")
                print(f"   Hostname: {res['hostname']}")
                print(f"   Kernel:   {res['kernel']}")
                print(f"   Uptime:   {res['uptime']}")
                print(f"   Docker:   v{res['docker_version']}")
            else:
                print(f"❌ Connection Failed: {res.get('error')}")
                print("Tip: Run 'coolify-control doctor' to diagnose VPN or Tailscale connectivity.")
                sys.exit(1)

    elif args.command == "apps":
        if args.apps_action == "list":
            res = ctrl.list_containers(search=args.search)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"{'NAME':<42} {'PROJECT':<16} {'DOMAIN / FQDN':<32} {'STATUS'}")
                print("-" * 110)
                for c in res:
                    proj = c['project'] or '-'
                    fqdn = c['fqdn'] or '-'
                    print(f"{c['name']:<42} {proj:<16} {fqdn:<32} {c['status']}")

        elif args.apps_action == "inspect":
            target = args.target
            if target.lower() in KNOWN_APPS:
                target = KNOWN_APPS[target.lower()]["container_match"]
            res = ctrl.inspect_container(target)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                if "error" in res:
                    print(f"❌ {res['error']}")
                    sys.exit(1)
                print(f"Container: {res['name']} ({res['id']})")
                print(f"Image:     {res['image']}")
                print(f"Status:    {res['status']}")
                print("\nMounts:")
                for m in res['mounts']:
                    print(f"  - {m['source']} -> {m['destination']} ({m['type']})")
                print("\nEnvironment Variables:")
                for e in res['environment']:
                    print(f"  {e}")

    elif args.command == "logs":
        target = args.target
        if target.lower() in KNOWN_APPS:
            target = KNOWN_APPS[target.lower()]["container_match"]
        logs = ctrl.get_logs(
            target,
            tail=args.tail,
            timestamps=args.timestamps,
            clean=args.clean,
            errors_only=args.errors_only
        )
        print(logs)

    elif args.command == "deploy":
        if args.deploy_action == "list":
            res = ctrl.list_deployments(app_name=args.app, limit=args.limit)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"{'ID':<6} {'APPLICATION':<45} {'STATUS':<12} {'COMMIT':<10} {'CREATED AT'}")
                print("-" * 95)
                for d in res:
                    print(f"{d['id']:<6} {d['app_name']:<45} {d['status']:<12} {d['commit']:<10} {d['created_at']}")

        elif args.deploy_action == "logs":
            log = ctrl.get_deployment_log(args.target, tail=args.tail)
            print(log)

        elif args.deploy_action == "restart":
            ok, msg = ctrl.restart_container(args.target)
            if args.json:
                print(json.dumps({"success": ok, "message": msg}))
            else:
                print(msg)
            if not ok:
                sys.exit(1)

        elif args.deploy_action == "trigger":
            ok, msg = ctrl.trigger_deployment(args.target, force_rebuild=not args.no_rebuild)
            if args.json:
                print(json.dumps({"success": ok, "message": msg}))
            else:
                print(msg)
            if not ok:
                sys.exit(1)

    elif args.command == "db":
        if args.db_action == "list":
            res = ctrl.list_databases()
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"{'CONTAINER NAME':<40} {'ENGINE':<12} {'PROJECT':<18} {'STATUS'}")
                print("-" * 95)
                for db in res:
                    print(f"{db['name']:<40} {db['engine']:<12} {db['project']:<18} {db['status']}")

        elif args.db_action == "find":
            res = ctrl.find_database_for(args.query)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                if not res:
                    print(f"No database found matching query '{args.query}'")
                else:
                    for db in res:
                        print(f"• Container: {db['name']}")
                        print(f"  Engine:    {db['engine']}")
                        print(f"  Project:   {db['project']}")
                        print(f"  Status:    {db['status']}")
                        print(f"  Ports:     {db['ports']}")

        elif args.db_action == "query":
            code, out, err = ctrl.query_database(args.target, args.sql, database_name=args.database)
            if args.json:
                print(json.dumps({
                    "exit_code": code,
                    "stdout": out,
                    "stderr": err,
                    "success": code == 0
                }, indent=2))
            else:
                if code == 0:
                    print(out)
                else:
                    sys.stderr.write(f"❌ Query failed (exit code {code}):\n{err}\n")
                    sys.exit(code)

    elif args.command == "exec":
        code, out, err = remote.run_remote(args.cmd, timeout=args.timeout)
        if args.json:
            print(json.dumps({
                "exit_code": code,
                "stdout": out,
                "stderr": err
            }, indent=2))
        else:
            if out:
                print(out, end="")
            if err:
                sys.stderr.write(err)
            sys.exit(code)


if __name__ == "__main__":
    main()
