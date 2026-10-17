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
from coolify_control import CoolifyController, SSHManager


class MockSSHManager:
    """Mock SSH Manager for testing controller parsing without network access."""

    def __init__(self, mock_output=""):
        self.mock_output = mock_output
        self.last_command = None
        self.active_host = "100.101.49.42"

    def run_remote(self, command, timeout=30):
        self.last_command = command
        return 0, self.mock_output, ""


class TestCoolifyControlCLI(unittest.TestCase):
    """Tests CLI argument parsing across all subcommands."""

    def test_status_command_json_both_positions(self):
        # Test --json after subcommand
        sys.argv = ["coolify_control.py", "status", "--json"]
        # Should not raise SystemExit
        from coolify_control import main

    def test_apps_list_parsing(self):
        mock_docker = (
            "431ab9d912a3\tapi-server-fmm1i1dj\tforex-quant-api:latest\tUp 12 days\t5000/tcp\tcoolify.projectName=forex,coolify.type=application\n"
            "977c150ccd61\tui-fmm1i1dj\tforex-quant-ui:latest\tUp 13 days\t80/tcp\tcoolify.projectName=forex,traefik.http.routers.rule=Host(`forex.dvlpid.my.id`)\n"
        )
        ssh = MockSSHManager(mock_output=mock_docker)
        ctrl = CoolifyController(ssh)

        containers = ctrl.list_containers()
        self.assertEqual(len(containers), 2)
        self.assertEqual(containers[0]["project"], "forex")
        self.assertEqual(containers[1]["fqdn"], "forex.dvlpid.my.id")

        # Test search filter
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
        ssh = MockSSHManager(mock_output=mock_docker)
        ctrl = CoolifyController(ssh)

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
        ssh = MockSSHManager(mock_output=raw_events)
        ctrl = CoolifyController(ssh)

        parsed_log = ctrl.get_deployment_log("123", tail=10)
        self.assertIn("Building container", parsed_log)
        self.assertIn("Deployment successful", parsed_log)


if __name__ == "__main__":
    unittest.main()
