import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import List, Tuple
from unittest import mock

from repochecker import main as repochecker_main


REPO_ROOT = Path(__file__).resolve().parents[1]
REPOCHECKER_SCRIPT = REPO_ROOT / "repochecker" / "main.py"
GIT = shutil.which("git")


class RepoCheckerUnitTestCase(unittest.TestCase):
    GLOBAL_FIELDS = (
        "update_remotes",
        "auto_pull",
        "force_pull",
        "submodules",
        "is_debug",
        "is_debug_git",
        "show_push",
        "show_pull",
        "show_short",
        "no_colors",
        "start_path",
        "tab_size",
        "directories_to_ignore",
    )

    def setUp(self) -> None:
        self._globals_snapshot = {}
        for field in self.GLOBAL_FIELDS:
            value = getattr(repochecker_main.Globals, field)
            self._globals_snapshot[field] = list(value) if isinstance(value, list) else value

        repochecker_main.Globals.update_remotes = False
        repochecker_main.Globals.auto_pull = False
        repochecker_main.Globals.force_pull = False
        repochecker_main.Globals.submodules = False
        repochecker_main.Globals.is_debug = False
        repochecker_main.Globals.is_debug_git = False
        repochecker_main.Globals.show_push = False
        repochecker_main.Globals.show_pull = False
        repochecker_main.Globals.show_short = False
        repochecker_main.Globals.no_colors = False
        repochecker_main.Globals.start_path = ""
        repochecker_main.Globals.tab_size = -1
        repochecker_main.Globals.directories_to_ignore = []

    def tearDown(self) -> None:
        for field, value in self._globals_snapshot.items():
            restored = list(value) if isinstance(value, list) else value
            setattr(repochecker_main.Globals, field, restored)

    def make_repo(self, root_path: str = r"D:\Temp\RepoChecker") -> repochecker_main.GitRepo:
        return repochecker_main.GitRepo(root_path)

    def make_current_branch(self, root_path: str = r"D:\Temp\RepoChecker") -> repochecker_main.GitBranch:
        return repochecker_main.GitBranch("* main", self.make_repo(root_path))


class RepoCheckerMarkerMatrixTests(RepoCheckerUnitTestCase):
    pass


class RepoCheckerGitExecMatrixTests(RepoCheckerUnitTestCase):
    pass


class RepoCheckerBranchStatusMatrixTests(RepoCheckerUnitTestCase):
    pass


class RepoCheckerSubmoduleMatrixTests(RepoCheckerUnitTestCase):
    def make_repo_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        repo_root = Path(temp_dir.name) / "repo-root"
        repo_root.mkdir(parents=True, exist_ok=True)
        return repo_root

    def test_init_repo_task_finds_submodules_before_branches(self) -> None:
        git_repo = mock.Mock()

        repochecker_main.init_repo_task(git_repo)

        self.assertEqual(
            git_repo.mock_calls,
            [mock.call.find_submodules(), mock.call.find_branches()],
        )

    def test_find_submodules_recurses_into_nested_gitmodules(self) -> None:
        repochecker_main.Globals.submodules = True
        repo_root = self.make_repo_root()
        child_path = Path(repo_root, "deps", "child")
        nested_path = Path(child_path, "nested")
        child_path.mkdir(parents=True, exist_ok=True)
        nested_path.mkdir(parents=True, exist_ok=True)

        git_outputs = {
            repochecker_main.normalize_path(str(repo_root)): ("submodule.child.path deps/child\n", 0),
            repochecker_main.normalize_path(str(child_path)): ("submodule.nested.path nested\n", 0),
            repochecker_main.normalize_path(str(nested_path)): ("", 1),
        }

        def fake_git_exec(path: str, args: str) -> Tuple[str, int]:
            return git_outputs.get(repochecker_main.normalize_path(path), ("", 1))

        repo = repochecker_main.GitRepo(str(repo_root))
        with mock.patch("repochecker.main.git_exec", side_effect=fake_git_exec):
            repo.find_submodules()

        self.assertEqual(len(repo.submodules), 1)
        self.assertEqual(len(repo.submodules[0].submodules), 1)
        self.assertEqual(
            repo.submodules[0].submodules[0].root_path,
            repochecker_main.normalize_path(str(nested_path)),
        )


@unittest.skipUnless(GIT, "git is required for filesystem edge-case tests")
class RepoCheckerInvalidGitIntegrationTests(RepoCheckerUnitTestCase):
    def make_scan_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        scan_root = Path(temp_dir.name) / "scan-root"
        scan_root.mkdir(parents=True, exist_ok=True)
        return scan_root

    def run_repochecker(self, start_path: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(REPOCHECKER_SCRIPT), "--no-colors", str(start_path)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_git(self, repo_path: Path, *args: str) -> subprocess.CompletedProcess:
        result = subprocess.run(
            [GIT, *args],
            cwd=repo_path,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def create_valid_git_repo(self, repo_path: Path) -> None:
        repo_path.mkdir(parents=True, exist_ok=True)
        self.run_git(repo_path, "init")
        self.run_git(repo_path, "config", "user.email", "tests@example.com")
        self.run_git(repo_path, "config", "user.name", "RepoChecker Tests")
        Path(repo_path, "tracked.txt").write_text("tracked\n", encoding="utf-8")
        self.run_git(repo_path, "add", "tracked.txt")
        self.run_git(repo_path, "commit", "-m", "initial")

    def create_valid_git_file_repo(self, repo_path: Path) -> None:
        self.create_valid_git_repo(repo_path)
        git_dir = Path(repo_path, ".git")
        redirected_git_dir = Path(repo_path.parent, f"{repo_path.name}.gitdir")
        shutil.move(str(git_dir), str(redirected_git_dir))
        git_pointer = f"gitdir: {redirected_git_dir.as_posix()}\n"
        git_dir.write_text(git_pointer, encoding="utf-8")

    def create_invalid_git_pointer_repo(self, repo_path: Path) -> None:
        repo_path.mkdir(parents=True, exist_ok=True)
        Path(repo_path, ".git").write_text("gitdir: missing/gitdir\n", encoding="utf-8")

    def create_invalid_git_dir_repo(self, repo_path: Path) -> None:
        repo_path.mkdir(parents=True, exist_ok=True)
        Path(repo_path, ".git").mkdir(parents=True, exist_ok=True)


_MARKER_DIR_CASES = [
    ("empty", []),
    ("git-only", [".git"]),
    ("src-only", ["src"]),
    ("docs-only", ["docs"]),
    ("git-and-src", [".git", "src"]),
    ("gitignore-name", [".gitignore"]),
    ("nested-git", ["nested", ".git"]),
    ("upper-git", [".GIT"]),
]

_MARKER_FILE_CASES = [
    ("empty", []),
    ("git-only", [".git"]),
    ("readme-only", ["README.md"]),
    ("gitignore-only", [".gitignore"]),
    ("git-and-readme", [".git", "README.md"]),
    ("upper-git", [".GIT"]),
    ("nested-file", ["nested.txt"]),
    ("config-file", ["config.ini"]),
]


def _make_marker_test(dir_entries: List[str], file_entries: List[str], expected: bool):
    def test(self: RepoCheckerMarkerMatrixTests) -> None:
        self.assertEqual(repochecker_main.has_git_repo_marker(dir_entries, file_entries), expected)

    return test


for dir_name, dir_entries in _MARKER_DIR_CASES:
    for file_name, file_entries in _MARKER_FILE_CASES:
        expected = ".git" in dir_entries or ".git" in file_entries
        test_name = f"test_has_git_repo_marker__{dir_name}__{file_name}"
        setattr(
            RepoCheckerMarkerMatrixTests,
            test_name,
            _make_marker_test(dir_entries, file_entries, expected),
        )


_GIT_EXEC_PATH_CASES = [
    ("cwd", "."),
    ("simple", r"D:\Temp\RepoChecker"),
    ("space", r"D:\Temp\Repo Checker"),
    ("home", r"~\RepoChecker Home"),
]

_GIT_EXEC_ARG_CASES = [
    ("branch", "branch"),
    ("status", "status -suno"),
    ("gitmodules", "config --file .gitmodules --get-regexp path"),
]


def _make_git_exec_success_test(path_value: str, arg_value: str):
    def test(self: RepoCheckerGitExecMatrixTests) -> None:
        fake_process = mock.Mock()
        fake_process.communicate.return_value = (b"stdout-value", b"")
        fake_process.returncode = 0

        with mock.patch("repochecker.main.subprocess.Popen", return_value=fake_process) as popen_mock:
            output, error_code = repochecker_main.git_exec(path_value, arg_value)

        self.assertEqual(output, "stdout-value")
        self.assertEqual(error_code, 0)
        popen_mock.assert_called_once()
        self.assertEqual(
            popen_mock.call_args.args[0],
            ["git", "-C", repochecker_main.normalize_path(path_value), *shlex.split(arg_value)],
        )

    return test


def _make_git_exec_oserror_test(path_value: str, arg_value: str):
    def test(self: RepoCheckerGitExecMatrixTests) -> None:
        with mock.patch(
            "repochecker.main.subprocess.Popen",
            side_effect=OSError("git launch failed"),
        ):
            output, error_code = repochecker_main.git_exec(path_value, arg_value)

        self.assertEqual(error_code, 1)
        self.assertIn("git launch failed", output)

    return test


for path_name, path_value in _GIT_EXEC_PATH_CASES:
    for arg_name, arg_value in _GIT_EXEC_ARG_CASES:
        setattr(
            RepoCheckerGitExecMatrixTests,
            f"test_git_exec_returns_stdout__{path_name}__{arg_name}",
            _make_git_exec_success_test(path_value, arg_value),
        )
        setattr(
            RepoCheckerGitExecMatrixTests,
            f"test_git_exec_handles_oserror__{path_name}__{arg_name}",
            _make_git_exec_oserror_test(path_value, arg_value),
        )


_STATUS_ATTR_CASES = [
    ("modified", "M", "modified"),
    ("added", "A", "added"),
    ("deleted", "D", "deleted"),
    ("renamed", "R", "renamed"),
    ("copied", "C", "copied"),
    ("updated", "U", "updated"),
    ("untracked", "??", "untracked"),
]

_STATUS_PATH_CASES = [
    ("plain", "tracked.txt"),
    ("nested", "src/main.py"),
    ("space", "folder with spaces/file name.txt"),
    ("deep", "a/b/c/value.md"),
    ("upper", "README.TXT"),
    ("hyphen", "name-with-hyphen.js"),
    ("dots", "name.with.dots.cfg"),
    ("numbered", "dir9/file_7.txt"),
]

_SHORT_STATUS_LINES = [
    "",
    " ",
    "?",
    "M",
    "A",
    "D",
    "R",
    "C",
    "U",
    "??",
    "M ",
    "A ",
    "D ",
    "R ",
    "C ",
    "U ",
    "\t",
    " \t",
    "\n",
    "  ",
]

_STATUS_ERROR_MESSAGES = [
    "fatal: not a git repository",
    "fatal: bad object HEAD",
    "fatal: index file corrupt",
    "fatal: unable to read tree",
    "fatal: ambiguous argument",
    "fatal: no such path",
    "fatal: detected dubious ownership",
    "fatal: could not parse HEAD",
    "fatal: object file is empty",
    "fatal: not a valid object name",
    "fatal: reference is not a tree",
    "fatal: cannot lock ref",
    "fatal: bad revision",
    "fatal: invalid pathspec",
    "fatal: repository broken",
    "fatal: failed to read refs",
    "fatal: invalid gitfile format",
    "fatal: misplaced alternates file",
    "fatal: missing object database",
    "fatal: worktree has invalid HEAD",
]


def _make_branch_status_mapping_test(status_value: str, target_attr: str, path_value: str):
    def test(self: RepoCheckerBranchStatusMatrixTests) -> None:
        branch = self.make_current_branch()
        branch.find_diffs_from_remote = mock.Mock(return_value=[])

        with mock.patch("repochecker.main.git_exec", return_value=(f"{status_value} {path_value}\n", 0)):
            branch.check_status()

        for attr_name in ("modified", "added", "deleted", "renamed", "copied", "updated", "untracked"):
            expected = [path_value] if attr_name == target_attr else []
            self.assertEqual(getattr(branch, attr_name), expected)

    return test


def _make_branch_short_line_test(line_value: str):
    def test(self: RepoCheckerBranchStatusMatrixTests) -> None:
        branch = self.make_current_branch()
        branch.find_diffs_from_remote = mock.Mock(return_value=[])

        with mock.patch("repochecker.main.git_exec", return_value=(line_value, 0)):
            branch.check_status()

        for attr_name in ("modified", "added", "deleted", "renamed", "copied", "updated", "untracked"):
            self.assertEqual(getattr(branch, attr_name), [])

    return test


def _make_branch_status_error_test(message_value: str):
    def test(self: RepoCheckerBranchStatusMatrixTests) -> None:
        branch = self.make_current_branch()
        branch.find_diffs_from_remote = mock.Mock()

        with mock.patch("repochecker.main.git_exec", return_value=(message_value, 128)):
            with mock.patch("builtins.print"):
                branch.check_status()

        branch.find_diffs_from_remote.assert_not_called()
        for attr_name in ("modified", "added", "deleted", "renamed", "copied", "updated", "untracked"):
            self.assertEqual(getattr(branch, attr_name), [])

    return test


for status_name, status_value, target_attr in _STATUS_ATTR_CASES:
    for path_name, path_value in _STATUS_PATH_CASES:
        setattr(
            RepoCheckerBranchStatusMatrixTests,
            f"test_check_status_maps_{status_name}__{path_name}",
            _make_branch_status_mapping_test(status_value, target_attr, path_value),
        )

for index, line_value in enumerate(_SHORT_STATUS_LINES):
    setattr(
        RepoCheckerBranchStatusMatrixTests,
        f"test_check_status_ignores_short_line__{index:02d}",
        _make_branch_short_line_test(line_value),
    )

for index, message_value in enumerate(_STATUS_ERROR_MESSAGES):
    setattr(
        RepoCheckerBranchStatusMatrixTests,
        f"test_check_status_stops_on_git_error__{index:02d}",
        _make_branch_status_error_test(message_value),
    )


_SUBMODULE_NAME_CASES = [
    ("basic", "basic"),
    ("hyphen", "feature-pack"),
    ("dots", "vendor.pkg"),
    ("nested", "deps/tools"),
    ("upper", "UPPER"),
    ("mixed", "Mixed.Name"),
    ("underscore", "module_one"),
    ("deep", "level1/level2"),
]

_SUBMODULE_PATH_CASES = [
    ("direct", "deps/basic"),
    ("space", "deps/space dir"),
    ("nested", "vendor/module"),
    ("sibling", "../sibling-sub"),
    ("dot-relative", "./local-sub"),
    ("deep", "deep/tree/item"),
    ("upper", "UPPER/Sub"),
    ("mixed", "mix-ed/name.one"),
]

_INVALID_GITMODULE_LINES = [
    "submodule",
    "submodule.bad",
    "submodule.bad.path",
    "submodulebad.path deps/bad",
    "module.bad.path deps/bad",
    "submodule.badpath deps/bad",
    "submodule.bad.paths deps/bad",
    "path deps/bad",
    "submodule..path",
    "submodule.bad.path",
    "invalid-entry",
    "just one token",
    "submodule.bad.path\t",
    "bad.key value",
    "submodulebad deps/bad",
    "submodule.bad. value",
]

_MISSING_SUBMODULE_PATHS = [
    "deps/missing-one",
    "deps/missing-two",
    "deps/missing three",
    "vendor/absent",
    "../outside-missing",
    "./still-missing",
    "deep/tree/missing",
    "UPPER/Missing",
    "mix-ed/missing.one",
    "pkg/missing-nine",
    "pkg/missing-ten",
    "pkg/missing-eleven",
    "pkg/missing-twelve",
    "pkg/missing-thirteen",
    "pkg/missing-fourteen",
    "pkg/missing-fifteen",
]


def _make_valid_submodule_test(submodule_name: str, relative_path: str):
    def test(self: RepoCheckerSubmoduleMatrixTests) -> None:
        repochecker_main.Globals.submodules = True
        repo_root = self.make_repo_root()
        expected_submodule_path = repochecker_main.normalize_path(os.path.join(str(repo_root), relative_path))
        Path(expected_submodule_path).mkdir(parents=True, exist_ok=True)

        root_path = repochecker_main.normalize_path(str(repo_root))
        git_output = f"submodule.{submodule_name}.path {relative_path}\n"

        def fake_git_exec(path: str, args: str) -> Tuple[str, int]:
            if repochecker_main.normalize_path(path) == root_path:
                return git_output, 0
            return "", 1

        repo = repochecker_main.GitRepo(str(repo_root))
        with mock.patch("repochecker.main.git_exec", side_effect=fake_git_exec):
            repo.find_submodules()

        self.assertEqual(len(repo.submodules), 1)
        submodule = repo.submodules[0]
        self.assertTrue(submodule.is_submodule)
        self.assertIs(submodule.parent, repo)
        self.assertEqual(submodule.root_path, expected_submodule_path)
        self.assertEqual(submodule.name, os.path.basename(expected_submodule_path))

    return test


def _make_invalid_gitmodules_line_test(line_value: str):
    def test(self: RepoCheckerSubmoduleMatrixTests) -> None:
        repochecker_main.Globals.submodules = True
        repo_root = self.make_repo_root()
        repo = repochecker_main.GitRepo(str(repo_root))

        with mock.patch("repochecker.main.git_exec", return_value=(f"{line_value}\n", 0)):
            with mock.patch("builtins.print"):
                repo.find_submodules()

        self.assertEqual(repo.submodules, [])

    return test


def _make_missing_submodule_path_test(relative_path: str):
    def test(self: RepoCheckerSubmoduleMatrixTests) -> None:
        repochecker_main.Globals.submodules = True
        repo_root = self.make_repo_root()
        repo = repochecker_main.GitRepo(str(repo_root))

        with mock.patch(
            "repochecker.main.git_exec",
            return_value=(f"submodule.missing.path {relative_path}\n", 0),
        ):
            with mock.patch("builtins.print"):
                repo.find_submodules()

        self.assertEqual(repo.submodules, [])

    return test


for submodule_name_name, submodule_name in _SUBMODULE_NAME_CASES:
    for path_name, relative_path in _SUBMODULE_PATH_CASES:
        setattr(
            RepoCheckerSubmoduleMatrixTests,
            f"test_find_submodules_resolves_{submodule_name_name}__{path_name}",
            _make_valid_submodule_test(submodule_name, relative_path),
        )

for index, line_value in enumerate(_INVALID_GITMODULE_LINES):
    setattr(
        RepoCheckerSubmoduleMatrixTests,
        f"test_find_submodules_rejects_invalid_line__{index:02d}",
        _make_invalid_gitmodules_line_test(line_value),
    )

for index, relative_path in enumerate(_MISSING_SUBMODULE_PATHS):
    setattr(
        RepoCheckerSubmoduleMatrixTests,
        f"test_find_submodules_skips_missing_path__{index:02d}",
        _make_missing_submodule_path_test(relative_path),
    )


_INTEGRATION_LAYOUT_CASES = [
    ("direct", ("repo",)),
    ("nested", ("nested", "repo")),
    ("space", ("space repo",)),
    ("nested-space", ("nested level", "space repo")),
]

_INTEGRATION_SCENARIOS = [
    ("valid-git-dir", "create_valid_git_repo", False),
    ("valid-git-file", "create_valid_git_file_repo", False),
    ("invalid-git-pointer", "create_invalid_git_pointer_repo", True),
    ("invalid-git-dir", "create_invalid_git_dir_repo", True),
]


def _make_integration_test(builder_name: str, layout_parts: Tuple[str, ...], expect_branch_error: bool):
    def test(self: RepoCheckerInvalidGitIntegrationTests) -> None:
        scan_root = self.make_scan_root()
        repo_path = scan_root.joinpath(*layout_parts)
        getattr(self, builder_name)(repo_path)

        result = self.run_repochecker(scan_root)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Found 1 repos...", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        if expect_branch_error:
            self.assertIn("Failed to get branches", result.stdout)
        else:
            self.assertNotIn("Failed to get branches", result.stdout)

    return test


for scenario_name, builder_name, expect_branch_error in _INTEGRATION_SCENARIOS:
    for layout_name, layout_parts in _INTEGRATION_LAYOUT_CASES:
        setattr(
            RepoCheckerInvalidGitIntegrationTests,
            f"test_cli_handles_{scenario_name}__{layout_name}",
            _make_integration_test(builder_name, layout_parts, expect_branch_error),
        )


if __name__ == "__main__":
    unittest.main()
