import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from repochecker import main as repochecker_main


REPO_ROOT = Path(__file__).resolve().parents[1]
REPOCHECKER_SCRIPT = REPO_ROOT / "repochecker" / "main.py"


class RepoCheckerCliTests(unittest.TestCase):
    def run_repochecker(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(REPOCHECKER_SCRIPT), *args],
            cwd=cwd or REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_help_prints_usage(self) -> None:
        result = self.run_repochecker("--help")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage:", result.stdout)
        self.assertIn("--force-pull", result.stdout)
        self.assertIn("-Json --json", result.stdout)

    def test_version_uses_package_metadata(self) -> None:
        result = self.run_repochecker("--version")

        self.assertEqual(result.returncode, 0)
        self.assertIn("repochecker - 3.1.0-1", result.stdout)
        self.assertIn("Saturno Software", result.stdout)

    def test_json_metadata_prints_saturno_contract(self) -> None:
        result = self.run_repochecker("--json")

        self.assertEqual(result.returncode, 0)
        metadata = json.loads(result.stdout)
        self.assertEqual(metadata["Schema"], "saturno-cli-metadata/v1")
        self.assertEqual(metadata["Name"], "repochecker")
        self.assertEqual(metadata["Version"], "3.1.0")
        self.assertTrue(metadata["Supports"]["JsonMetadata"])
        self.assertFalse(metadata["Supports"]["ChangesDirectory"])
        self.assertIn("scan", [command["Name"] for command in metadata["Commands"]])

    def test_json_metadata_alias_is_supported(self) -> None:
        result = self.run_repochecker("-Json")

        self.assertEqual(result.returncode, 0)
        metadata = json.loads(result.stdout)
        self.assertEqual(metadata["Schema"], "saturno-cli-metadata/v1")

    def test_json_mode_returns_error_envelope_with_runtime_args(self) -> None:
        result = self.run_repochecker("--json", "--remote")

        self.assertEqual(result.returncode, 1)
        error_payload = json.loads(result.stderr)
        self.assertEqual(error_payload["Schema"], "saturno-cli-error/v1")
        self.assertEqual(error_payload["Code"], "cli.json-metadata-only")

    def test_metadata_helpers_stay_in_sync_with_text_outputs(self) -> None:
        metadata = repochecker_main.get_cli_metadata()

        self.assertEqual(metadata["UsageText"], repochecker_main.get_help_str())
        self.assertEqual(metadata["VersionText"], repochecker_main.get_version_text())
        self.assertIn("show-push", [command["Name"] for command in metadata["Commands"]])

    def test_normalize_path_expands_to_absolute_path(self) -> None:
        normalized = repochecker_main.normalize_path(".")

        self.assertTrue(os.path.isabs(normalized))

    def test_git_branch_local_dirty_detection(self) -> None:
        repo = repochecker_main.GitRepo(str(REPO_ROOT))
        branch = repochecker_main.GitBranch("* main", repo)

        self.assertTrue(branch.is_current)
        self.assertFalse(branch.is_local_dirty())

        branch.modified.append("README.md")
        self.assertTrue(branch.is_local_dirty())

    @unittest.skipUnless(shutil.which("git"), "git is required for scan tests")
    def test_scan_temp_git_repo_runs_successfully(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            git_repo = temp_path / "sample"
            git_repo.mkdir()
            subprocess.run(["git", "init"], cwd=git_repo, text=True, capture_output=True, check=False)

            result = self.run_repochecker("--no-colors", str(temp_path))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Found", result.stdout)


if __name__ == "__main__":
    unittest.main()
