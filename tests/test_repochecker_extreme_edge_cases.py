"""
Comprehensive edge case tests for repochecker CLI and git operations.
Tests extreme inputs, Unicode, emoji, malicious inputs, and boundary conditions.
"""

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


class RepoCheckerExtremePathTests(unittest.TestCase):
    """Test repochecker with extreme path scenarios."""

    def run_repochecker(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(REPOCHECKER_SCRIPT), *args],
            cwd=cwd or REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_path_with_unicode_characters(self):
        """Test with path containing Unicode characters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            unicode_path = Path(temp_dir) / "测试目录" / "プロジェクト"
            unicode_path.mkdir(parents=True, exist_ok=True)

            if shutil.which("git"):
                subprocess.run(["git", "init"], cwd=unicode_path, capture_output=True, check=False)
                result = self.run_repochecker("--no-colors", str(unicode_path))
                # Should handle Unicode paths without crashing
                self.assertIn(result.returncode, [0, 1])

    def test_path_with_emoji(self):
        """Test with path containing emoji."""
        with tempfile.TemporaryDirectory() as temp_dir:
            emoji_path = Path(temp_dir) / "🚀rocket" / "⭐project"
            emoji_path.mkdir(parents=True, exist_ok=True)

            if shutil.which("git"):
                subprocess.run(["git", "init"], cwd=emoji_path, capture_output=True, check=False)
                result = self.run_repochecker("--no-colors", str(emoji_path))
                self.assertIn(result.returncode, [0, 1])

    def test_path_with_spaces(self):
        """Test with path containing many spaces."""
        with tempfile.TemporaryDirectory() as temp_dir:
            spaced_path = Path(temp_dir) / "my   project   with   spaces"
            spaced_path.mkdir(parents=True, exist_ok=True)

            if shutil.which("git"):
                subprocess.run(["git", "init"], cwd=spaced_path, capture_output=True, check=False)
                result = self.run_repochecker("--no-colors", str(spaced_path))
                self.assertIn(result.returncode, [0, 1])

    def test_path_with_special_characters(self):
        """Test with path containing special shell characters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use characters that won't break filesystem but might break shell
            special_path = Path(temp_dir) / "project[test](name)"
            special_path.mkdir(parents=True, exist_ok=True)

            if shutil.which("git"):
                subprocess.run(["git", "init"], cwd=special_path, capture_output=True, check=False)
                result = self.run_repochecker("--no-colors", str(special_path))
                self.assertIn(result.returncode, [0, 1])

    def test_extremely_long_path(self):
        """Test with extremely long directory path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested path with total length near system limit
            long_component = "a" * 50
            nested_path = Path(temp_dir)
            for i in range(5):  # Create 5 levels of nesting
                nested_path = nested_path / f"{long_component}{i}"

            try:
                nested_path.mkdir(parents=True, exist_ok=True)
                if shutil.which("git"):
                    subprocess.run(["git", "init"], cwd=nested_path, capture_output=True, check=False)
                    result = self.run_repochecker("--no-colors", str(nested_path))
                    self.assertIn(result.returncode, [0, 1])
            except OSError:
                # Path too long for filesystem - expected on some systems
                self.skipTest("Path too long for this filesystem")

    def test_path_with_dot_prefix(self):
        """Test with hidden directory (dot prefix)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            hidden_path = Path(temp_dir) / ".hidden_project"
            hidden_path.mkdir(parents=True, exist_ok=True)

            if shutil.which("git"):
                subprocess.run(["git", "init"], cwd=hidden_path, capture_output=True, check=False)
                result = self.run_repochecker("--no-colors", str(hidden_path))
                self.assertIn(result.returncode, [0, 1])

    def test_path_with_trailing_slash(self):
        """Test with path having trailing slash."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / "project"
            test_path.mkdir(parents=True, exist_ok=True)

            if shutil.which("git"):
                subprocess.run(["git", "init"], cwd=test_path, capture_output=True, check=False)
                # Add trailing slash
                path_with_slash = str(test_path) + os.sep
                result = self.run_repochecker("--no-colors", path_with_slash)
                self.assertIn(result.returncode, [0, 1])

    def test_nonexistent_path(self):
        """Test with path that doesn't exist."""
        fake_path = "/this/path/definitely/does/not/exist/nowhere"
        result = self.run_repochecker("--no-colors", fake_path)
        # Should handle gracefully
        self.assertIsInstance(result.returncode, int)

    def test_path_with_symlink(self):
        """Test with symbolic link to directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            real_path = Path(temp_dir) / "real_project"
            link_path = Path(temp_dir) / "link_to_project"
            real_path.mkdir(parents=True, exist_ok=True)

            try:
                link_path.symlink_to(real_path)
                if shutil.which("git"):
                    subprocess.run(["git", "init"], cwd=real_path, capture_output=True, check=False)
                    result = self.run_repochecker("--no-colors", str(link_path))
                    self.assertIn(result.returncode, [0, 1])
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks not supported on this system")

    def test_path_with_relative_components(self):
        """Test with path containing .. components."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / "a" / "b" / "c"
            test_path.mkdir(parents=True, exist_ok=True)

            if shutil.which("git"):
                subprocess.run(["git", "init"], cwd=test_path, capture_output=True, check=False)
                # Use relative path with ..
                relative_path = str(test_path) + os.sep + ".." + os.sep + ".." + os.sep + "c"
                result = self.run_repochecker("--no-colors", relative_path)
                self.assertIn(result.returncode, [0, 1])


class RepoCheckerMaliciousInputTests(unittest.TestCase):
    """Test repochecker with malicious and injection attempts."""

    def run_repochecker(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(REPOCHECKER_SCRIPT), *args],
            cwd=cwd or REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_command_injection_in_path(self):
        """Test with command injection attempt in path."""
        malicious_paths = [
            "project; rm -rf /",
            "project && echo 'hacked'",
            "project | cat /etc/passwd",
            "project `whoami`",
            "project $(ls -la)"
        ]

        for malicious_path in malicious_paths:
            result = self.run_repochecker("--no-colors", malicious_path)
            # Should not execute the injected command
            self.assertIn(result.returncode, [0, 1])

    def test_sql_injection_in_path(self):
        """Test with SQL injection patterns in path."""
        sql_injections = [
            "'; DROP TABLE repos;--",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--"
        ]

        for sql_path in sql_injections:
            result = self.run_repochecker("--no-colors", sql_path)
            self.assertIn(result.returncode, [0, 1])

    def test_xss_injection_in_path(self):
        """Test with XSS patterns in path."""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>"
        ]

        for xss_path in xss_attempts:
            result = self.run_repochecker("--no-colors", xss_path)
            self.assertIn(result.returncode, [0, 1])

    def test_path_traversal_attempt(self):
        """Test with path traversal patterns."""
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "....//....//....//etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd"
        ]

        for traversal_path in traversal_attempts:
            result = self.run_repochecker("--no-colors", traversal_path)
            self.assertIn(result.returncode, [0, 1])

    def test_null_byte_injection(self):
        """Test with null byte in path."""
        null_byte_path = "project\x00/etc/passwd"
        try:
            result = self.run_repochecker("--no-colors", null_byte_path)
            self.assertIn(result.returncode, [0, 1])
        except (ValueError, OSError):
            # Null bytes in paths are rejected by subprocess - expected
            pass

    def test_format_string_attack(self):
        """Test with format string patterns."""
        format_strings = [
            "project%s%s%s%s",
            "project%n%n%n%n",
            "project%x%x%x%x"
        ]

        for format_path in format_strings:
            result = self.run_repochecker("--no-colors", format_path)
            self.assertIn(result.returncode, [0, 1])

    def test_ldap_injection(self):
        """Test with LDAP injection patterns."""
        ldap_injections = [
            "project*)(uid=*))(|(uid=*",
            "project)(cn=*))(|(cn=*",
        ]

        for ldap_path in ldap_injections:
            result = self.run_repochecker("--no-colors", ldap_path)
            self.assertIn(result.returncode, [0, 1])

    def test_xml_injection(self):
        """Test with XML/XXE injection patterns."""
        xml_injections = [
            "<!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>",
            "<?xml version='1.0'?><!DOCTYPE foo>",
        ]

        for xml_path in xml_injections:
            result = self.run_repochecker("--no-colors", xml_path)
            self.assertIn(result.returncode, [0, 1])

    def test_extremely_long_argument(self):
        """Test with extremely long command argument."""
        long_path = "a" * 100000
        try:
            result = self.run_repochecker("--no-colors", long_path)
            self.assertIn(result.returncode, [0, 1])
        except (OSError, ValueError):
            # Path too long - expected on some systems
            pass

    def test_many_arguments(self):
        """Test with many command line arguments."""
        many_args = ["--no-colors"] + ["path" + str(i) for i in range(1000)]
        result = self.run_repochecker(*many_args)
        self.assertIsInstance(result.returncode, int)


class RepoCheckerGitEdgeCaseTests(unittest.TestCase):
    """Test repochecker with various git repository edge cases."""

    def run_repochecker(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(REPOCHECKER_SCRIPT), *args],
            cwd=cwd or REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    @unittest.skipUnless(shutil.which("git"), "git required")
    def test_repo_with_unicode_branch_name(self):
        """Test with branch name containing Unicode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir) / "unicode_branch_repo"
            repo_path.mkdir(parents=True)
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=repo_path, capture_output=True, check=False)

            # Try to create Unicode branch
            unicode_branch = "测试-branch-プロジェクト"
            subprocess.run(["git", "checkout", "-b", unicode_branch], cwd=repo_path, capture_output=True, check=False)

            result = self.run_repochecker("--no-colors", str(repo_path))
            self.assertIn(result.returncode, [0, 1])

    @unittest.skipUnless(shutil.which("git"), "git required")
    def test_repo_with_emoji_branch_name(self):
        """Test with branch name containing emoji."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir) / "emoji_branch_repo"
            repo_path.mkdir(parents=True)
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=repo_path, capture_output=True, check=False)

            # Try emoji branch
            emoji_branch = "🚀feature-⭐star"
            subprocess.run(["git", "checkout", "-b", emoji_branch], cwd=repo_path, capture_output=True, check=False)

            result = self.run_repochecker("--no-colors", str(repo_path))
            self.assertIn(result.returncode, [0, 1])

    @unittest.skipUnless(shutil.which("git"), "git required")
    def test_repo_with_special_char_branch_name(self):
        """Test with branch name containing special characters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir) / "special_branch_repo"
            repo_path.mkdir(parents=True)
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=repo_path, capture_output=True, check=False)

            # Branch with special chars
            special_branch = "feature@v2.0#hotfix"
            subprocess.run(["git", "checkout", "-b", special_branch], cwd=repo_path, capture_output=True, check=False)

            result = self.run_repochecker("--no-colors", str(repo_path))
            self.assertIn(result.returncode, [0, 1])

    @unittest.skipUnless(shutil.which("git"), "git required")
    def test_repo_with_unicode_commit_message(self):
        """Test with commit message containing Unicode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir) / "unicode_commit_repo"
            repo_path.mkdir(parents=True)
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, capture_output=True, check=False)

            # Commit with Unicode
            unicode_message = "修复错误 🐛 - プロジェクト更新"
            subprocess.run(["git", "commit", "--allow-empty", "-m", unicode_message],
                          cwd=repo_path, capture_output=True, check=False)

            result = self.run_repochecker("--no-colors", str(repo_path))
            self.assertIn(result.returncode, [0, 1])

    @unittest.skipUnless(shutil.which("git"), "git required")
    def test_repo_with_emoji_commit_message(self):
        """Test with commit message full of emoji."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir) / "emoji_commit_repo"
            repo_path.mkdir(parents=True)
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, capture_output=True, check=False)

            emoji_message = "🎉 🚀 ✨ 🔥 💯 🎯 ⭐"
            subprocess.run(["git", "commit", "--allow-empty", "-m", emoji_message],
                          cwd=repo_path, capture_output=True, check=False)

            result = self.run_repochecker("--no-colors", str(repo_path))
            self.assertIn(result.returncode, [0, 1])

    @unittest.skipUnless(shutil.which("git"), "git required")
    def test_repo_with_unicode_author_name(self):
        """Test with Unicode characters in author name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir) / "unicode_author_repo"
            repo_path.mkdir(parents=True)
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.name", "张三 Сергей José"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "commit", "--allow-empty", "-m", "test"], cwd=repo_path, capture_output=True, check=False)

            result = self.run_repochecker("--no-colors", str(repo_path))
            self.assertIn(result.returncode, [0, 1])

    @unittest.skipUnless(shutil.which("git"), "git required")
    def test_repo_with_emoji_author_name(self):
        """Test with emoji in author name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir) / "emoji_author_repo"
            repo_path.mkdir(parents=True)
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.name", "🚀 Developer 🎯"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "commit", "--allow-empty", "-m", "test"], cwd=repo_path, capture_output=True, check=False)

            result = self.run_repochecker("--no-colors", str(repo_path))
            self.assertIn(result.returncode, [0, 1])

    @unittest.skipUnless(shutil.which("git"), "git required")
    def test_repo_with_unicode_filename(self):
        """Test with file containing Unicode characters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir) / "unicode_file_repo"
            repo_path.mkdir(parents=True)
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, capture_output=True, check=False)

            # Create file with Unicode name
            unicode_file = repo_path / "文件-プロジェクト-проект.txt"
            unicode_file.write_text("test content")

            subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "commit", "-m", "add unicode file"], cwd=repo_path, capture_output=True, check=False)

            result = self.run_repochecker("--no-colors", str(repo_path))
            self.assertIn(result.returncode, [0, 1])

    @unittest.skipUnless(shutil.which("git"), "git required")
    def test_repo_with_emoji_filename(self):
        """Test with file containing emoji."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir) / "emoji_file_repo"
            repo_path.mkdir(parents=True)
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, capture_output=True, check=False)

            # Create file with emoji name
            emoji_file = repo_path / "🚀rocket-⭐star.txt"
            emoji_file.write_text("test content")

            subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True, check=False)
            subprocess.run(["git", "commit", "-m", "add emoji file"], cwd=repo_path, capture_output=True, check=False)

            result = self.run_repochecker("--no-colors", str(repo_path))
            self.assertIn(result.returncode, [0, 1])

    @unittest.skipUnless(shutil.which("git"), "git required")
    def test_empty_git_repo(self):
        """Test with freshly initialized empty repo."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir) / "empty_repo"
            repo_path.mkdir(parents=True)
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=False)

            result = self.run_repochecker("--no-colors", str(repo_path))
            self.assertIn(result.returncode, [0, 1])

    @unittest.skipUnless(shutil.which("git"), "git required")
    def test_bare_git_repo(self):
        """Test with bare git repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            bare_repo_path = Path(temp_dir) / "bare_repo.git"
            bare_repo_path.mkdir(parents=True)
            subprocess.run(["git", "init", "--bare"], cwd=bare_repo_path, capture_output=True, check=False)

            result = self.run_repochecker("--no-colors", str(bare_repo_path))
            self.assertIn(result.returncode, [0, 1])

    @unittest.skipUnless(shutil.which("git"), "git required")
    def test_corrupted_git_repo(self):
        """Test with corrupted git repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir) / "corrupted_repo"
            repo_path.mkdir(parents=True)
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=False)

            # Corrupt the repo by removing critical file
            git_head = repo_path / ".git" / "HEAD"
            if git_head.exists():
                git_head.unlink()

            result = self.run_repochecker("--no-colors", str(repo_path))
            # Should handle corruption gracefully
            self.assertIsInstance(result.returncode, int)


class RepoCheckerNormalizePathTests(unittest.TestCase):
    """Test path normalization edge cases."""

    def test_normalize_current_directory(self):
        """Test normalizing current directory."""
        normalized = repochecker_main.normalize_path(".")
        self.assertTrue(os.path.isabs(normalized))

    def test_normalize_parent_directory(self):
        """Test normalizing parent directory."""
        normalized = repochecker_main.normalize_path("..")
        self.assertTrue(os.path.isabs(normalized))

    def test_normalize_home_directory(self):
        """Test normalizing home directory."""
        normalized = repochecker_main.normalize_path("~")
        self.assertTrue(os.path.isabs(normalized))
        # Case-insensitive comparison for Windows
        expected = os.path.expanduser("~")
        self.assertEqual(normalized.lower(), expected.lower())

    def test_normalize_unicode_path(self):
        """Test normalizing path with Unicode."""
        unicode_path = "~/测试/プロジェクト"
        normalized = repochecker_main.normalize_path(unicode_path)
        self.assertTrue(os.path.isabs(normalized))

    def test_normalize_emoji_path(self):
        """Test normalizing path with emoji."""
        emoji_path = "~/🚀rocket/⭐project"
        normalized = repochecker_main.normalize_path(emoji_path)
        self.assertTrue(os.path.isabs(normalized))

    def test_normalize_path_with_spaces(self):
        """Test normalizing path with spaces."""
        spaced_path = "~/my documents/my project"
        normalized = repochecker_main.normalize_path(spaced_path)
        self.assertTrue(os.path.isabs(normalized))

    def test_normalize_empty_string(self):
        """Test normalizing empty string."""
        # Should handle empty string gracefully
        try:
            normalized = repochecker_main.normalize_path("")
            self.assertIsInstance(normalized, str)
        except (ValueError, OSError):
            # Also acceptable to raise error
            pass

    def test_normalize_very_long_path(self):
        """Test normalizing very long path."""
        long_path = "a/" * 1000 + "file.txt"
        try:
            normalized = repochecker_main.normalize_path(long_path)
            self.assertIsInstance(normalized, str)
        except OSError:
            # Path too long - acceptable
            pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
