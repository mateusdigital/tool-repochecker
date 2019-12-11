#!/usr/bin/env python3
import os;
import os.path;
import glob;
import shlex;
import subprocess;
from pathlib import Path;
import pdb;
from cowtermcolor import *;

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
    git_paths = [];
    tab_size = -1;


##----------------------------------------------------------------------------##
## Log Functions                                                              ##
##----------------------------------------------------------------------------##
##------------------------------------------------------------------------------
def log_debug(fmt, *args):
    formatted = fmt.format(*args);
    print("[DEBUG] ", formatted);

##------------------------------------------------------------------------------
def log_error(fmt, *args):
    formatted = fmt.format(*args);
    print("[ERROR] ", formatted);

##------------------------------------------------------------------------------
def log_info(fmt, *args):
    # pdb.set_trace();
    formatted = fmt.format(*args);
    print(formatted);


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
    if(tab_size > 0):
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
    return os.path.abspath(os.path.normpath(os.path.normcase(path)));

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
        log_error("Failed running {0}", cmd);
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
## Color Functions                                                            ##
##----------------------------------------------------------------------------##
def BR(a): return colored(a, bg=ON_RED);

def FR(a): return colored(a, fg=RED);
def FY(a): return colored(a, fg=YELLOW);
def FG(a): return colored(a, fg=GREEN);


def C_clean_repo(s): return colored(s, fg=GREEN  );
def C_dirty_repo(s): return colored(s, fg=MAGENTA);

def colorize_repo_name(git_repo):
    pretty_name = os.path.basename(git_repo.root_path);
    if(git_repo.is_dirty):
        pretty_name = C_dirty_repo(pretty_name);
    else:
        pretty_name = C_clean_repo(pretty_name);

    prefix = "[Submodule]" if git_repo.is_submodule else "[Repo]";
    path = colored(git_repo.root_path, bg=ON_GREY);
    return "{0} {1} ".format(prefix, pretty_name, path);

def colorize_branch_name(branch_name):
    return colored(branch_name, CYAN);



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
        status_result, error_code = git_exec(self.repo.root_path, "status -s");
        ## @todo(stdmatt): error handling...

        for line in status_result.split("\n"):
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

        # self.diffs_to_push = self.find_diffs_from_remote("{1}..{0}/{1}", remote_name);
        # self.diffs_to_pull = self.find_diffs_from_remote("{0}/{1}..{1}", remote_name);

        self.diffs_to_pull = self.find_diffs_from_remote("{1}..{0}/{1}", remote_name);
        self.diffs_to_push = self.find_diffs_from_remote("{0}/{1}..{1}", remote_name);

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
    def __init__(self, root_path, is_submodule = False):
        Globals.git_paths.append(normalize_path(root_path));

        self.root_path      = root_path;
        self.is_submodule   = is_submodule;
        self.branches       = [];
        self.current_branch = None;
        self.is_dirty       = False;

        self.submodules = [];
        self.find_submodules();

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
                pdb.set_trace();

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
            if(branch is None):
                pdb.set_trace();

            len_modified  = len(branch.modified  );
            len_added     = len(branch.added     );
            len_deleted   = len(branch.deleted   );
            len_renamed   = len(branch.renamed   );
            len_copied    = len(branch.copied    );
            len_updated   = len(branch.updated   );
            len_untracked = len(branch.untracked );

            status_str = "";
            if(len_added    ): status_str += "{0}({1}) ".format(FG(GIT_STATUS_ADDED    ),  len_added     );
            if(len_copied   ): status_str += "{0}({1}) ".format(FG(GIT_STATUS_COPIED   ),  en_copied     );
            if(len_deleted  ): status_str += "{0}({1}) ".format(FR(GIT_STATUS_DELETED  ),  len_deleted   );
            if(len_modified ): status_str += "{0}({1}) ".format(FY(GIT_STATUS_MODIFIED ),  len_modified  );
            if(len_renamed  ): status_str += "{0}({1}) ".format(FY(GIT_STATUS_RENAMED  ),  len_renamed   );
            if(len_updated  ): status_str += "{0}({1}) ".format(FY(GIT_STATUS_UPDATED  ),  len_updated   );
            if(len_untracked): status_str += "{0}({1}) ".format(BR(GIT_STATUS_UNTRACKED),  len_untracked );

            branch_name = colorize_branch_name(branch.name);
            tab_indent();
            tab_print("{0} - {1}".format(branch_name, status_str));

            tab_indent();
            to_push = branch.diffs_to_push;
            tab_print("To Push: ({0})".format(len(to_push)));

            tab_indent();
            for line in to_push:
                tab_print("[{0}]".format(line));
            tab_unindent();

            tab_unindent(); ## to push

            tab_indent();
            to_pull = branch.diffs_to_pull;
            tab_print("To Pull: ({0})".format(len(to_pull)));

            tab_indent();
            for line in to_pull:
                tab_print(line);
            tab_unindent();
            tab_unindent(); ## to push


            tab_unindent();

        for submodule in self.submodules:
            submodule.print_result();
        tab_unindent();


##----------------------------------------------------------------------------##
## Entry Point                                                                ##
##----------------------------------------------------------------------------##
def main():
    start_path = os.path.join(
        get_home_path(),
        # "Documents/Projects/stdmatt"
        "Documents/Projects/stdmatt/games"
    );
    # start_path = "..";

    ##
    ## Discover the repositories.
    git_repos = [];
    for git_path in Path(start_path).rglob(".git"):
        git_root_path = normalize_path(os.path.dirname(git_path));

        if(git_root_path in Globals.git_paths):
            log_debug("Path is a submodule - Path: ({0})", git_root_path);
            continue;

        log_debug("Found repository at ({0})", git_root_path);
        git_repo = GitRepo(git_root_path);
        git_repos.append(git_repo);


    ##
    ## Update the Repositories.
    log_info("Found {0} repos...", len(git_repos));
    repos_to_show = [];
    for i in range(0, len(git_repos)):
        log_debug("Updating Repositiory ({0} of {1})", i+1, len(git_repos));

        git_repo = git_repos[i];
        git_repo.find_branches();
        git_repo.check_status();

        if(git_repo.is_dirty):
            repos_to_show.append(git_repo);

    ##
    ## Show the results.
    log_info("Results of ({0}) repos...", len(repos_to_show));
    for git_repo in repos_to_show:
        git_repo.print_result();

main();
