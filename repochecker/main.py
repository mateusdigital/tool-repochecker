#!/usr/bin/env python3
import os;
import os.path;
import glob;
import shlex;
import subprocess;
import sys;
import pdb;
import argparse;

from pathlib import Path;


##----------------------------------------------------------------------------##
## Constants                                                                  ##
##----------------------------------------------------------------------------##
GIT_STATUS_MODIFIED  = "M";
GIT_STATUS_ADDED     = "A";
GIT_STATUS_DELETED   = "D";
GIT_STATUS_RENAMED   = "R";
GIT_STATUS_COPIED    = "C";
GIT_STATUS_UPDATED   = "U";
GIT_STATUS_UNTRACKED = "??";


##----------------------------------------------------------------------------##
## Globals                                                                    ##
##----------------------------------------------------------------------------##
class Globals:
    ##
    ## Command Line Args.
    color_enabled  = True;
    is_debug       = False;
    start_path     = "";
    update_remotes = False;

    ##
    ## Housekeeping
    already_searched_git_path = [];
    tab_size                  = -1;


##----------------------------------------------------------------------------##
## Color Functions                                                            ##
##----------------------------------------------------------------------------##
from .cowtermcolor import *;

class Colors(object):
    def __init__(self):
        ColorMode.mode = ColorMode.ALWAYS;

        self._bred = Color(bg=ON_RED);
        self._fred = Color(fg=RED);
        self._fgreen = Color(fg=GREEN);
        self._fgray = Color(fg=BRIGHT_BLACK);
        self._fyellow = Color(fg=YELLOW);
        self._fcyan = Color(fg=CYAN);
        self._fwhite = Color(fg=WHITE);


_Color = Colors();

def BRed   (text): return _Color._bred   (text);
def FRed   (text): return _Color._fred   (text);
def FGreen (text): return _Color._fgreen (text);
def FGray  (text): return _Color._fgray  (text);
def FYellow(text): return _Color._fyellow(text);
def FCyan  (text): return _Color._fcyan  (text);
def FWhite (text): return _Color._fwhite (text);

def colorize_repo_name(git_repo):
    pretty_name = os.path.basename(git_repo.root_path);
    if(git_repo.is_dirty):
        pretty_name = FGreen(pretty_name);
    else:
        pretty_name = FM(pretty_name);

    prefix = "[Submodule]" if git_repo.is_submodule else "[Repo]";
    path   = git_repo.root_path;

    return "{0} {1} ".format(prefix, pretty_name, path);


##----------------------------------------------------------------------------##
## Log Functions                                                              ##
##----------------------------------------------------------------------------##
##------------------------------------------------------------------------------
def log_debug(fmt, *args):
    if(not Globals.is_debug):
        return;

    formatted = fmt.format(*args);
    print("[DEBUG] ", formatted);

def log_debug_error(fmt, *args):
    if(not Globals.is_debug):
        return;

    formatted = fmt.format(*args);
    print("[DEBUG-ERROR] ", formatted);

##------------------------------------------------------------------------------
def log_error(fmt, *args):
    formatted = fmt.format(*args);
    print("[ERROR] ", formatted);

##------------------------------------------------------------------------------
def log_info(fmt, *args):
    # pdb.set_trace();
    formatted = fmt.format(*args);
    print(formatted);

def log_fatal(fmt, *args):
    if(len(args) != 0):
        formatted = fmt.format(*args);
    else:
        formatted = fmt;
    print(formatted);
    exit(1);

##----------------------------------------------------------------------------##
## Print Functions                                                            ##
##----------------------------------------------------------------------------##
def tab_indent():
    Globals.tab_size += 1;

##------------------------------------------------------------------------------
def tab_unindent():
    Globals.tab_size -= 1;

##------------------------------------------------------------------------------
def tab_print(*args):
    tabs     = "";
    args_str = str(*args);
    if(Globals.tab_size > 0):
        tabs = ("    " * Globals.tab_size);

    print("{0}{1}".format(tabs, args_str));


##----------------------------------------------------------------------------##
## OS / Path Functions                                                        ##
##----------------------------------------------------------------------------##
##------------------------------------------------------------------------------
def get_home_path():
    return os.path.abspath(os.path.expanduser("~"));

##------------------------------------------------------------------------------
def normalize_path(path):
    path = os.path.expanduser(path);
    path = os.path.normcase(path);
    path = os.path.normpath(path);
    path = os.path.abspath(path);
    return path;

##----------------------------------------------------------------------------##
## Git Functions                                                              ##
##----------------------------------------------------------------------------##
##------------------------------------------------------------------------------
def git_exec(path, args):
    path           = normalize_path(path);
    cmd            = "git -C \"%s\" %s" % (path, args);
    cmd_components = shlex.split(cmd);
    # log_debug("{0}", cmd);

    p = subprocess.Popen(cmd_components, stdout=subprocess.PIPE, stderr=subprocess.PIPE);
    output, errors = p.communicate();

    if(p.returncode):
        ## log_debug_error("Failed running {0}", cmd);
        return "", p.returncode;

    return output.decode('utf-8'), p.returncode;

##------------------------------------------------------------------------------
def git_clean_branch_name(branch_name):
    clean_name = branch_name.strip(" ").strip("*").strip(" ");
    return clean_name;

##------------------------------------------------------------------------------
def git_is_current_branch(branch_name):
    clean_name = branch_name.strip(" ");
    return clean_name.startswith("*");


##----------------------------------------------------------------------------##
## Types                                                                      ##
##----------------------------------------------------------------------------##
##------------------------------------------------------------------------------
class GitBranch:
    ##--------------------------------------------------------------------------
    def __init__(self, branch_name, repo):
        self.name       = git_clean_branch_name(branch_name);
        self.is_current = git_is_current_branch(branch_name);
        self.repo       = repo;

        self.is_dirty  = False;
        self.modified  = [];
        self.added     = [];
        self.deleted   = [];
        self.renamed   = [];
        self.copied    = [];
        self.updated   = [];
        self.untracked = [];

        self.diffs_to_pull = [];
        self.diffs_to_push = [];

    ##--------------------------------------------------------------------------
    def check_status(self):
        ##
        ## Find the local modifications.
        status_result, error_code = git_exec(self.repo.root_path, "status -suno");
        ## @todo(stdmatt): error handling...
        for line in status_result.split("\n"):
            if(len(line) == 0 or not self.is_current):
                continue;

            self.is_dirty = True;

            status = line[0:2].strip(" ");
            path   = line[2: ].strip(" ");

            if(status == GIT_STATUS_MODIFIED):
                self.modified.append(path);
            elif(status == GIT_STATUS_ADDED):
                self.added.append(path);
            elif(status == GIT_STATUS_DELETED):
                self.deleted.append(path);
            elif(status == GIT_STATUS_RENAMED):
                self.renamed.append(path);
            elif(status == GIT_STATUS_COPIED):
                self.copied.append(path);
            elif(status == GIT_STATUS_UPDATED):
                self.updated.append(path);
            elif(status == GIT_STATUS_UNTRACKED):
                self.untracked.append(path);

        ##
        ## Find the differences to remote.
        ## @TODO(stdmatt): I'm just checking for origin right now that's my
        ## main use case... I need to understand better how to check for
        ## other remotes as well.
        remote_name = "origin";

        self.diffs_to_pull = self.find_diffs_from_remote("{1}..{0}/{1}", remote_name);
        self.diffs_to_push = self.find_diffs_from_remote("{0}/{1}..{1}", remote_name);

        if(len(self.diffs_to_pull) != 0 or len(self.diffs_to_push) != 0):
            self.is_dirty = True;

    ##--------------------------------------------------------------------------
    def find_diffs_from_remote(self, fmt, remote_name):
        fmt = fmt.format(remote_name, self.name);
        status_result, error_code = git_exec(
            self.repo.root_path,
            "log {0} --oneline".format(fmt)
        );

        if(error_code != 0):
            return [];

        diffs = [];
        for line in status_result.split("\n"):
            line = line.strip();
            if(len(line) == 0):
                continue;

            diffs.append(line);

        return diffs;

##------------------------------------------------------------------------------
class GitRepo:
    ##--------------------------------------------------------------------------
    def __init__(self, root_path, is_submodule=False):
        Globals.already_searched_git_path.append(normalize_path(root_path));
        log_debug(
            "Found {2} Path:({0}) - Submodule: ({1})",
            root_path,
            is_submodule,
            "Submodule" if is_submodule else "Repo"
        );

        self.name           = os.path.basename(root_path);
        self.root_path      = root_path;
        self.is_submodule   = is_submodule;
        self.branches       = [];
        self.current_branch = None;
        self.is_dirty       = False;
        self.submodules     = [];

        self.find_submodules();

    ##--------------------------------------------------------------------------
    def update_remotes(self):
        if(Globals.update_remotes):
            log_debug("Updating remotes...");
            git_exec(self.root_path, "remote update")

    ##--------------------------------------------------------------------------
    def find_submodules(self):
        result, error_code = git_exec(
            self.root_path,
            "config --file .gitmodules --name-only --get-regexp path"
        );

        if(error_code != 0):
            return;

        lines = result.split("\n");
        for line in lines:
            line = line.strip(" ");
            if(len(line) == 0):
                continue;

            submodule_path = line[len("submodule."):-(len(".path"))];
            submodule_path = os.path.join(self.root_path, submodule_path);

            if(not os.path.isdir(submodule_path)):
                msg = "\n".join([
                    "While scanning repository submodules"
                    , "repochecker found a submodule entry that doesn't correspond to a valid path."
                    , "Repository Path        : {0}"
                    , "Submodule Entry        : {1}"
                    , "Submodule Invalid Path : {2}"
                ]);
                msg = msg.format(self.root_path, line, submodule_path);
                log_fatal(msg);

            log_debug(
                "Found submodule of ({0}) at ({1})",
                self.root_path,
                submodule_path
            );

            git_repo = GitRepo(submodule_path, True);
            self.submodules.append(git_repo);

    ##--------------------------------------------------------------------------
    def find_branches(self):
        result, error_code = git_exec(self.root_path, "branch");
        ## todo(stdmatt): error handling...
        for branch_name in result.splitlines():
            branch = GitBranch(branch_name, self);
            self.branches.append(branch);
            if(branch.is_current):
                self.current_branch = branch;

        for submodule in self.submodules:
            submodule.find_branches();

    ##--------------------------------------------------------------------------
    def check_status(self):
        for branch in self.branches:
            branch.check_status();
            if(branch.is_dirty):
                self.is_dirty = True;

        for submodule in self.submodules:
            submodule.check_status();

    ##--------------------------------------------------------------------------
    def print_result(self):
        if(not self.is_dirty):
            return;

        tab_indent();

        repo_pretty_name = colorize_repo_name(self);
        tab_print(repo_pretty_name);

        for branch in self.branches:
            if(not branch.is_dirty):
                continue;

            if(branch is None):
                pdb.set_trace();

            def _concat_status_str(diff, color_func, msg):
                if (len(diff) == 0):
                    return "";
                return "{0}({1}) ".format(color_func(msg), color_func(len(diff)));

            def _print_branch_name(branch_name, status_str):
                branch_name = FGray(branch_name);
                if(len(status_str) != 0):
                    tab_print("{0} - {1}".format(branch_name, status_str));
                else:
                    tab_print("{0}".format(branch_name));

            def _print_push_pull_info(diff, msg):
                if(len(diff) == 0):
                    return;

                tab_indent();
                tab_print("{0}: ({1})".format(msg, FCyan(len(diff))));

                for line in diff:
                    tab_indent();

                    components = line.split(" ");
                    sha = FRed(components[0]);
                    msg = FWhite(" ".join(components[1:]));

                    tab_print("[{0} {1}]".format(sha, msg));
                    tab_unindent();

                tab_unindent();

            status_str = "";
            # branch.modified = [1,1,2,]
            # branch.added = [1,1,2,]
            # branch.deleted = [1,1,2,]
            # branch.renamed = [1, 3 , 4 ]
            # branch.copied = [1,1,2,]
            # branch.updated =[1,1,2,]
            # branch.untracked = [1,1,2,]

            status_str += _concat_status_str(branch.modified, FYellow, GIT_STATUS_MODIFIED);
            status_str += _concat_status_str(branch.added, FGreen, GIT_STATUS_ADDED);
            status_str += _concat_status_str(branch.deleted, FRed, GIT_STATUS_DELETED);
            status_str += _concat_status_str(branch.renamed, FYellow, GIT_STATUS_RENAMED);
            status_str += _concat_status_str(branch.copied, FYellow, GIT_STATUS_COPIED);
            status_str += _concat_status_str(branch.updated, FYellow, GIT_STATUS_UPDATED);
            status_str += _concat_status_str(branch.untracked, BRed, GIT_STATUS_UNTRACKED);

            tab_indent();
            _print_branch_name(branch.name, status_str);
            _print_push_pull_info(branch.diffs_to_push, FGreen("To Push"));
            _print_push_pull_info(branch.diffs_to_pull, FYellow("To Pull"));
            tab_unindent();

        for submodule in self.submodules:
            submodule.print_result();
        tab_unindent();

def parse_args():
    parser = argparse.ArgumentParser(description="git repository checker");
    ## Debug.
    parser.add_argument(
        "--debug",
        dest="is_debug",
        action="store_true",
        default=False
    );
    ## Colors.
    parser.add_argument(
        "--no-colors",
        dest="color_enabled",
        action="store_false",
        default=True
    );
    ## Update Remotes.
    parser.add_argument(
        "--remote",
        dest="update_remote",
        action="store_true",
        default=False
    );
    ## Start Path.
    parser.add_argument(
        "path",
        default=os.getcwd()
    );

    return parser.parse_args();

##----------------------------------------------------------------------------##
## Entry Point                                                                ##
##----------------------------------------------------------------------------##
def main():
    ##
    ## Parse the command line arguments.
    args = parse_args();

    Globals.is_debug       = args.is_debug;
    Globals.color_enabled  = args.color_enabled
    Globals.start_path     = normalize_path(args.path);
    Globals.update_remotes = args.update_remote;

    ## Globals.start_path = "/Users/stdmatt/Documents/Projects/stdmatt/demos/startfield"
    ##
    ## Discover the repositories.
    git_repos = [];
    for git_path in Path(Globals.start_path).rglob(".git"):
        git_root_path = normalize_path(os.path.dirname(git_path));
        if(git_root_path in Globals.already_searched_git_path):
            log_debug("Path is already visited- Path: ({0})", git_root_path);
            continue;

        git_repo = GitRepo(git_root_path);
        git_repos.append(git_repo);

    ##
    ## Update the Repositories.
    log_info("Found {0} repos...", len(git_repos));

    repos_to_show = [];
    for i in range(0, len(git_repos)):
        log_debug("Updating Repository ({0} of {1})", i+1, len(git_repos));

        git_repo = git_repos[i];

        git_repo.update_remotes();
        git_repo.find_branches();
        git_repo.check_status();

    for i in range(0, len(git_repos)):
        git_repo = git_repos[i];
        git_repo.print_result();

