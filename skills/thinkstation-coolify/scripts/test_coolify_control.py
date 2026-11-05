#!/usr/bin/env python3
"""
Unit tests for coolify_control.py (ThinkStation Coolify & Database Controller)
Hermetic, offline, zero-network tests validating CLI arguments, parsing, and engine detection.
"""

import unittest
import sys
from pathlib import Path

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

import coolify_control
from coolify_control import CoolifyController, SSHManager, strip_ansi


class MockRemoteManager:
    """Mock Remote Manager for testing controller parsing without network access."""

    def __init__(self, mock_output=""):
        self.mock_output = mock_output
        self.last_command = None
        self.active_host = "100.101.49.42"
        self.active_transport = "mesh"
        self.mesh_node = "100.101.49.42:8484"
        self.mesh_token = "mock-token"
        self.proxy = "socks5h://127.0.0.1:1055"

    def run_remote(self, command, timeout=30):
        self.last_command = command
        return 0, self.mock_output, ""


class TestCoolifyControlCLI(unittest.TestCase):
    """Tests CLI argument parsing and controller logic across subcommands."""

    def test_status_command_json_both_positions(self):
        sys.argv = ["coolify-control", "status", "--json"]
        from coolify_control import main

    def test_apps_list_parsing(self):
        mock_docker = (
            "431ab9d912a3\tapi-server-fmm1i1dj\tforex-quant-api:latest\tUp 12 days\t5000/tcp\tcoolify.projectName=forex,coolify.type=application\n"
            "977c150ccd61\tui-fmm1i1dj\tforex-quant-ui:latest\tUp 13 days\t80/tcp\tcoolify.projectName=forex,traefik.http.routers.rule=Host(`forex.dvlpid.my.id`)\n"
        )
        remote = MockRemoteManager(mock_output=mock_docker)
        ctrl = CoolifyController(remote)

        containers = ctrl.list_containers()
        self.assertEqual(len(containers), 2)
        self.assertEqual(containers[0]["project"], "forex")
        self.assertEqual(containers[1]["fqdn"], "forex.dvlpid.my.id")

        filtered = ctrl.list_containers(search="ui")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["name"], "ui-fmm1i1dj")

    def test_database_engine_detection(self):
        mock_docker = (
            "c16ccb041d27\tcoolify-db\tpostgres:15-alpine\tUp 2 days\t5432/tcp\tcoolify.type=database\n"
            "a0e584ab261e\th139vp1fyu5dz7sgnq6wg984\t0320de35118b\tUp 13 days\t3306/tcp\tcoolify.type=database\n"
            "a0c110cc893e\tcoolify-redis\tredis:7-alpine\tUp 2 days\t6379/tcp\tcoolify.type=database\n"
            "da31fc92348f\tffhz4t4ki2gkwq5ryl10xf5b\tmariadb:11\tUp 13 days\t3306/tcp\tcoolify.type=database\n"
        )
        remote = MockRemoteManager(mock_output=mock_docker)
        ctrl = CoolifyController(remote)

        dbs = ctrl.list_databases()
        self.assertEqual(len(dbs), 4)

        engines = {d["name"]: d["engine"] for d in dbs}
        self.assertEqual(engines["coolify-db"], "postgres")
        self.assertEqual(engines["h139vp1fyu5dz7sgnq6wg984"], "mysql")
        self.assertEqual(engines["coolify-redis"], "redis")
        self.assertEqual(engines["ffhz4t4ki2gkwq5ryl10xf5b"], "mariadb")

    def test_deployment_log_json_parsing(self):
        raw_events = (
            '[{"output":"Building container","timestamp":"2026-10-16T10:00:00Z"},'
            '{"output":"Deployment successful","timestamp":"2026-10-16T10:01:00Z"}]'
        )
        remote = MockRemoteManager(mock_output=raw_events)
        ctrl = CoolifyController(remote)

        parsed_log = ctrl.get_deployment_log("123", tail=10)
        self.assertIn("Building container", parsed_log)
        self.assertIn("Deployment successful", parsed_log)

    def test_strip_ansi_and_clean_logs(self):
        colored_log = "\x1b[32mSUCCESS:\x1b[0m Service started\n: OPENROUTER PROCESSING\nReal message"
        cleaned = strip_ansi(colored_log)
        self.assertNotIn("\x1b[32m", cleaned)
        self.assertIn("SUCCESS: Service started", cleaned)

        remote = MockRemoteManager(mock_output=colored_log)
        ctrl = CoolifyController(remote)
        logs = ctrl.get_logs("some-container", clean=True)
        self.assertNotIn(": OPENROUTER PROCESSING", logs)
        self.assertIn("Real message", logs)

    def test_trigger_deployment(self):
        remote = MockRemoteManager(mock_output="QUEUED:dep-uuid-12345")
        ctrl = CoolifyController(remote)
        ok, msg = ctrl.trigger_deployment("cerdas")
        self.assertTrue(ok)
        self.assertIn("dep-uuid-12345", msg)


if __name__ == "__main__":
    unittest.main()
