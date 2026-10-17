#!/usr/bin/env python3
"""
ThinkStation Coolify Controller & Database Query CLI Tool
Part of the `thinkstation-coolify` skill.

Automates SSH operations to ThinkStation (Coolify server for *.dvlpid.my.id):
- Auto-provisions SSH keys from Infisical if missing
- Agnostically lists, inspects, and tails logs for any Coolify application/container
- Monitors deployment queue & build logs
- Discovers database containers (PostgreSQL, MySQL, MariaDB, Redis)
- Executes queries against target databases with auto-extracted credentials
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

DEFAULT_KEY_PATH = Path.home() / ".ssh" / "id_ed25519_agent"
DEFAULT_USER = "server"
TAILSCALE_HOST = "100.101.49.42"
LAN_HOST = "192.168.0.136"
INFISICAL_PROJECT_ID = "f13379e0-9661-4f8e-81ef-0e81d1502da1"
INFISICAL_ENV = "dev"


class SSHManager:
    """Manages resilient SSH connections to ThinkStation via Tailscale or LAN."""

    def __init__(self, key_path: Path = DEFAULT_KEY_PATH, user: str = DEFAULT_USER):
        self.key_path = key_path
        self.user = user
        self.active_host: Optional[str] = None

    def ensure_key_exists(self) -> None:
        """Restores the SSH private key from Infisical if it does not exist locally."""
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
            self.key_path.write_text(res.stdout)
            self.key_path.chmod(0o600)
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to auto-restore SSH key via Infisical: {e}\n")

    def resolve_host(self) -> str:
        """Determines whether Tailscale IP or LAN IP is currently reachable."""
        if self.active_host:
            return self.active_host

        self.ensure_key_exists()

        # Check Tailscale first
        for host in [TAILSCALE_HOST, LAN_HOST]:
            test_cmd = [
                "ssh", "-i", str(self.key_path),
                "-o", "ConnectTimeout=3",
                "-o", "StrictHostKeyChecking=accept-new",
                "-o", "BatchMode=yes",
                "-p", "22",
                f"{self.user}@{host}",
                "echo PING_OK"
            ]
            try:
                res = subprocess.run(test_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
                if res.returncode == 0 and "PING_OK" in res.stdout:
                    self.active_host = host
                    return host
            except Exception:
                continue

        # Default fallback to Tailscale
        self.active_host = TAILSCALE_HOST
        return self.active_host

    def run_remote(self, command: str, timeout: Optional[int] = 30) -> Tuple[int, str, str]:
        """Executes a command on ThinkStation over SSH."""
        host = self.resolve_host()
        ssh_cmd = [
            "ssh", "-i", str(self.key_path),
            "-o", "ConnectTimeout=5",
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "BatchMode=yes",
            "-p", "22",
            f"{self.user}@{host}",
            command
        ]
        try:
            res = subprocess.run(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
            return res.returncode, res.stdout, res.stderr
        except subprocess.TimeoutExpired:
            return 124, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return 1, "", str(e)


class CoolifyController:
    """Agnostic controller for Docker containers, Coolify metadata, and databases."""

    def __init__(self, ssh: SSHManager):
        self.ssh = ssh

    def get_status(self) -> Dict[str, Any]:
        """Fetches host status, Docker health, and Coolify version."""
        cmd = "hostname && uname -r && uptime -p && docker version --format '{{.Server.Version}}'"
        code, out, err = self.ssh.run_remote(cmd)
        lines = out.strip().splitlines()
        return {
            "connected": code == 0,
            "host": self.ssh.active_host,
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
        code, out, _ = self.ssh.run_remote(cmd)
        if code != 0:
            return []

        containers = []
        for line in out.strip().splitlines():
            parts = line.split('\t')
            if len(parts) < 6:
                continue
            cid, name, image, status, ports, labels_str = parts[:6]

            # Parse Coolify-relevant labels
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
        cmd = f"docker inspect {target} --format '{{{{json .}}}}'"
        code, out, err = self.ssh.run_remote(cmd)
        if code != 0:
            return {"error": err.strip() or f"Container {target} not found"}

        try:
            data = json.loads(out)
            config = data.get("Config", {})
            env_list = config.get("Env", [])
            # Filter sensitive values slightly or keep clean
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

    def get_logs(self, target: str, tail: int = 100, timestamps: bool = False) -> str:
        """Fetches logs for a container or application."""
        ts_flag = "-t" if timestamps else ""
        cmd = f"docker logs {ts_flag} --tail {tail} {target}"
        _, out, err = self.ssh.run_remote(cmd, timeout=30)
        return out if out else err

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
        code, out, _ = self.ssh.run_remote(cmd)
        if code != 0:
            return []

        deployments = []
        lines = out.strip().splitlines()
        if len(lines) <= 1:
            return []

        for line in lines[1:]:  # skip header
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
        code, out, err = self.ssh.run_remote(cmd)
        if code != 0 or not out.strip():
            return f"No deployment log found for '{deploy_id_or_app}'"

        raw = out.strip()
        # Parse JSON event format if returned by Coolify
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

    def restart_container(self, target: str) -> Tuple[bool, str]:
        """Restarts a container safely."""
        cmd = f"docker restart {target}"
        code, out, err = self.ssh.run_remote(cmd, timeout=30)
        if code == 0:
            return True, f"Successfully restarted {target}"
        return False, err.strip()

    def list_databases(self) -> List[Dict[str, Any]]:
        """Finds all database containers on the server."""
        containers = self.list_containers()
        dbs = []
        db_keywords = ["postgres", "mysql", "mariadb", "redis", "mongo", "clickhouse", "timescale"]

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
                # Classify database engine
                engine = "unknown"
                for k in ["postgres", "timescale", "mysql", "mariadb", "redis", "mongo", "clickhouse"]:
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
        Executes a SQL query inside a database container with auto-extracted credentials.
        Supports PostgreSQL, MySQL, MariaDB, and Redis.
        """
        # Inspect container to detect engine & environment variables
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
            return self.ssh.run_remote(cmd)

        # 2. MySQL / MariaDB
        if "mysql" in image or "mariadb" in image or "MYSQL_ROOT_PASSWORD" in env_dict or "MARIADB_USER" in env_dict:
            user = env_dict.get("MYSQL_USER") or env_dict.get("MARIADB_USER") or "root"
            password = env_dict.get("MYSQL_PASSWORD") or env_dict.get("MARIADB_PASSWORD") or env_dict.get("MYSQL_ROOT_PASSWORD") or ""
            db = database_name or env_dict.get("MYSQL_DATABASE") or env_dict.get("MARIADB_DATABASE") or ""

            pass_flag = f"-p'{password}'" if password else ""
            db_flag = db if db else ""
            escaped_sql = sql.replace('"', '\\"')
            cmd = f'docker exec {db_target} mysql -u {user} {pass_flag} {db_flag} -e "{escaped_sql}"'
            return self.ssh.run_remote(cmd)

        # 3. Redis
        if "redis" in image or "valkey" in image or "redis" in name:
            password = env_dict.get("REDIS_PASSWORD", "")
            auth_flag = f"-a '{password}'" if password else ""
            cmd = f'docker exec {db_target} redis-cli {auth_flag} {sql}'
            return self.ssh.run_remote(cmd)

        return 1, "", f"Unsupported database engine for container {db_target} ({image})"


def main():
    common_p = argparse.ArgumentParser(add_help=False)
    common_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    parser = argparse.ArgumentParser(
        prog="coolify_control.py",
        description="ThinkStation Coolify & Database Agnostic Management CLI",
        parents=[common_p]
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. Status
    subparsers.add_parser("status", parents=[common_p], help="Check server, Docker, and SSH connectivity status")

    # 2. Apps
    apps_p = subparsers.add_parser("apps", parents=[common_p], help="Container and application discovery")
    apps_sub = apps_p.add_subparsers(dest="apps_action", required=True)
    list_p = apps_sub.add_parser("list", parents=[common_p], help="List running applications and containers")
    list_p.add_argument("--search", "-s", help="Filter by name, project, or domain")
    inspect_p = apps_sub.add_parser("inspect", parents=[common_p], help="Inspect container environment & mounts")
    inspect_p.add_argument("target", help="Container name or ID")

    # 3. Logs
    logs_p = subparsers.add_parser("logs", parents=[common_p], help="Fetch logs from any container")
    logs_p.add_argument("target", help="Container name or ID")
    logs_p.add_argument("--tail", "-n", type=int, default=100, help="Number of lines (default: 100)")
    logs_p.add_argument("--timestamps", "-t", action="store_true", help="Show timestamps")

    # 4. Deploy
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

    # 5. Database
    db_p = subparsers.add_parser("db", parents=[common_p], help="Database discovery and query execution")
    db_sub = db_p.add_subparsers(dest="db_action", required=True)
    db_sub.add_parser("list", parents=[common_p], help="List all database containers on the server")
    db_find_p = db_sub.add_parser("find", parents=[common_p], help="Find database for a project or app")
    db_find_p.add_argument("query", help="Project name, app name, or keyword")
    db_query_p = db_sub.add_parser("query", parents=[common_p], help="Execute SQL inside a database container")
    db_query_p.add_argument("target", help="Database container name or ID")
    db_query_p.add_argument("--sql", required=True, help="SQL statement to execute")
    db_query_p.add_argument("--database", "-d", help="Database name override")

    # 6. Exec
    exec_p = subparsers.add_parser("exec", parents=[common_p], help="Execute arbitrary command on ThinkStation")
    exec_p.add_argument("cmd", help="Command string to run")

    args = parser.parse_args()

    ssh = SSHManager()
    ctrl = CoolifyController(ssh)

    # Dispatch commands
    if args.command == "status":
        res = ctrl.get_status()
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            if res["connected"]:
                print(f"✅ ThinkStation Connected via {res['host']}")
                print(f"   Hostname: {res['hostname']}")
                print(f"   Kernel:   {res['kernel']}")
                print(f"   Uptime:   {res['uptime']}")
                print(f"   Docker:   v{res['docker_version']}")
            else:
                print(f"❌ Connection Failed: {res.get('error')}")
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
            res = ctrl.inspect_container(args.target)
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
        logs = ctrl.get_logs(args.target, tail=args.tail, timestamps=args.timestamps)
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
        code, out, err = ssh.run_remote(args.cmd)
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
