import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_JSON = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
BUILD_NUMBER = 41
RELEASE_NAME = f"{PACKAGE_JSON['name']}-{PACKAGE_JSON['version']}-{BUILD_NUMBER}"
BUILD_DIR = REPO_ROOT / "__BUILD" / RELEASE_NAME
DIST_DIR = REPO_ROOT / "__DIST" / RELEASE_NAME
PWSH = shutil.which("pwsh")


@unittest.skipUnless(PWSH, "pwsh is required for release-layout tests")
class RepoCheckerReleaseLayoutTests(unittest.TestCase):
    def tearDown(self) -> None:
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
        shutil.rmtree(DIST_DIR, ignore_errors=True)

    def run_pwsh(self, script_path: Path, extra_args: list[str] | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        command = [
            PWSH,
            "-NoLogo",
            "-NoProfile",
            "-File",
            str(script_path),
            "-ProjectRoot",
            str(REPO_ROOT),
            "-BuildNumber",
            str(BUILD_NUMBER),
        ]
        if extra_args:
            command.extend(extra_args)
        return subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def build_release(self) -> subprocess.CompletedProcess[str]:
        return self.run_pwsh(REPO_ROOT / "Scripts" / "build.ps1", [
            "-BuildOutputDir", str(BUILD_DIR),
            "-ReleaseName", RELEASE_NAME,
        ])

    def package_release(self) -> subprocess.CompletedProcess[str]:
        build_result = self.build_release()
        self.assertEqual(build_result.returncode, 0, build_result.stderr)

        package_result = self.run_pwsh(REPO_ROOT / "Scripts" / "package.ps1", [
            "-BuildOutputDir", str(BUILD_DIR),
            "-PackageOutputDir", str(DIST_DIR),
            "-ReleaseName", RELEASE_NAME,
        ])
        self.assertEqual(package_result.returncode, 0, package_result.stderr)
        return package_result

    def test_build_stages_package_ready_app_layout(self) -> None:
        result = self.build_release()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((BUILD_DIR / "App" / "repochecker.py").is_file())
        self.assertTrue((BUILD_DIR / "App" / "repochecker.ps1").is_file())
        self.assertTrue((BUILD_DIR / "App" / "repochecker.sh").is_file())
        self.assertTrue((BUILD_DIR / "package.json").is_file())
        self.assertTrue((BUILD_DIR / "install.sh").is_file())
        self.assertTrue((BUILD_DIR / "install.ps1").is_file())

    def test_package_preserves_release_layout(self) -> None:
        self.package_release()

        self.assertTrue((DIST_DIR / "App" / "repochecker.py").is_file())
        self.assertTrue((DIST_DIR / "App" / "repochecker.ps1").is_file())
        self.assertTrue((DIST_DIR / "App" / "repochecker.sh").is_file())
        self.assertTrue((DIST_DIR / "package.json").is_file())

    def test_packaged_powershell_install_uses_dist_layout(self) -> None:
        self.package_release()

        with tempfile.TemporaryDirectory() as temp_home:
            env = os.environ.copy()
            env["HOME"] = temp_home
            env["USERPROFILE"] = temp_home

            result = subprocess.run(
                [
                    PWSH,
                    "-NoLogo",
                    "-NoProfile",
                    "-File",
                    str(DIST_DIR / "install.ps1"),
                ],
                cwd=DIST_DIR,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            install_root = Path(temp_home) / ".saturnosoftware" / "repochecker"
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((install_root / "bin" / "repochecker.py").is_file())
            self.assertTrue((install_root / "bin" / "repochecker.ps1").is_file())
            self.assertTrue((install_root / "package.json").is_file())
            self.assertTrue((install_root / "config").is_dir())
            self.assertTrue((install_root / "data").is_dir())

            version_result = subprocess.run(
                [sys.executable, str(install_root / "bin" / "repochecker.py"), "-v"],
                cwd=install_root / "bin",
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(version_result.returncode, 0, version_result.stderr)
            self.assertIn(f"repochecker - {PACKAGE_JSON['version']}-{PACKAGE_JSON['build']}", version_result.stdout)


if __name__ == "__main__":
    unittest.main()
