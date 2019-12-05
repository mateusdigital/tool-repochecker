#!/usr/bin/env python3
import os;
import os.path;
import glob;
import shlex;
import subprocess;
from pathlib import Path;
import pdb;
import cowtermcolor;

GIT_STATUS_MODIFIED  = "M";
GIT_STATUS_ADDED     = "A";
GIT_STATUS_DELETED   = "D";
GIT_STATUS_RENAMED   = "R";
GIT_STATUS_COPIED    = "C";
GIT_STATUS_UPDATED   = "U";
GIT_STATUS_UNTRACKED = "??";

git_paths = [];


def log_debug(fmt, *args):
    formatted = fmt.format(*args);
    print("[DEBUG] ", formatted);

def log_error(fmt, *args):
    return;
    formatted = fmt.format(*args);
    print("[ERROR] ", formatted);

def log_info(fmt, *args):
    # pdb.set_trace();
    formatted = fmt.format(*args);
    print(formatted);

def get_home_path():
    return os.path.abspath(os.path.expanduser("~"));

def normalize_path(path):
    return os.path.abspath(os.path.normpath(os.path.normcase(path)));

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

def clean_branch_name(branch_name):
    clean_name = branch_name.strip(" ").strip("*").strip(" ");
    return clean_name;

def is_current_branch(branch_name):
    clean_name = branch_name.strip(" ");
    return clean_name.startswith("*");


def BR(a): return cowtermcolor.on_red(a) + cowtermcolor.reset();

def FR(a): return cowtermcolor.red(a) + cowtermcolor.reset();
def FY(a): return cowtermcolor.yellow(a) + cowtermcolor.reset();
def FG(a): return cowtermcolor.green(a) + cowtermcolor.reset();


def C_clean_repo(s): return cowtermcolor.green  (s) + cowtermcolor.reset();
def C_dirty_repo(s): return cowtermcolor.magenta(s) + cowtermcolor.reset();

def colorize_repo_name(git_repo):
    # os.path.basename
    pretty_name = (git_repo.root_path);
    if(git_repo.is_dirty):
        return C_dirty_repo(pretty_name);
    return C_clean_repo(pretty_name);



class GitBranch:
    def __init__(self, branch_name, repo):
        self.name       = clean_branch_name(branch_name);
        self.is_current = is_current_branch(branch_name);
        self.repo       = repo;

        self.is_dirty  = False;
        self.modified  = [];
        self.added     = [];
        self.deleted   = [];
        self.renamed   = [];
        self.copied    = [];
        self.updated   = [];
        self.untracked = [];

    def check_status(self):
        if(not self.is_current):
            return;

        status_result = git_exec(self.repo.root_path, "status -s");
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

class GitRepo:
    def __init__(self, root_path):
        global git_paths;
        git_paths.append(normalize_path(root_path));

        self.root_path      = root_path;
        self.branches       = [];
        self.current_branch = None;
        self.is_dirty       = False;

        self.submodules = [];
        self.find_submodules();

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
            log_debug(
                "Found submodule of ({0}) at ({1})",
                self.root_path,
                submodule_path
            );

            git_repo = GitRepo(submodule_path);
            self.submodules.append(git_repo);

    def get_branches(self):
        result = git_exec(self.root_path, "branch");
        for branch_name in result.splitlines():
            branch = GitBranch(branch_name, self);
            self.branches.append(branch);
            if(branch.is_current):
                self.current_branch = branch;

    def check_status(self):
        for branch in self.branches:
            branch.check_status();
            if(branch.is_dirty):
                self.is_dirty = True;


def main():
    global git_paths;
    start_path = os.path.join(
        get_home_path(),
        "Documents/Projects/stdmatt/games/xonix"
    );

    ##
    ## Discover the repositories.
    git_repos = [];
    for git_path in Path(start_path).rglob(".git"):
        git_root_path = normalize_path(os.path.dirname(git_path));

        if(git_root_path in git_paths):
            log_debug("Path is a submodule - Path: ({0})", git_root_path);
            continue;

        log_debug("Found repository at ({0})", git_root_path);
        git_repo = GitRepo(git_root_path);
        git_repos.append(git_repo);


    return;
    ##
    ## Update the Repositories.
    log_info("Found {0} repos...", len(git_repos));
    repos_to_show = [];
    for i in range(0, len(git_repos)):
        log_debug("Updating Repositiory ({0} of {1})", i+1, len(git_repos));

        git_repo = git_repos[i];
        git_repo.get_branches();
        git_repo.check_status();

        if(git_repo.is_dirty):
            repos_to_show.append(git_repo);

    ##
    ## Show the results.
    log_info("Results of ({0}) repos...", len(repos_to_show));
    for git_repo in repos_to_show:
        branch = git_repo.current_branch;
        len_modified  = len(branch.modified  );
        len_added     = len(branch.added     );
        len_deleted   = len(branch.deleted   );
        len_renamed   = len(branch.renamed   );
        len_copied    = len(branch.copied    );
        len_updated   = len(branch.updated   );
        len_untracked = len(branch.untracked );

        status_str = "";
        if(len_added    ): status_str += "{0}({1}) ".format(FG(GIT_STATUS_ADDED   ),  len_added   );
        if(len_copied   ): status_str += "{0}({1}) ".format(FG(GIT_STATUS_COPIED  ),  en_copied  );
        if(len_deleted  ): status_str += "{0}({1}) ".format(FR(GIT_STATUS_DELETED ),  len_deleted );
        if(len_modified ): status_str += "{0}({1}) ".format(FY(GIT_STATUS_MODIFIED),  len_modified);
        if(len_renamed  ): status_str += "{0}({1}) ".format(FY(GIT_STATUS_RENAMED ),  len_renamed );
        if(len_updated  ): status_str += "{0}({1}) ".format(FY(GIT_STATUS_UPDATED ),  len_updated );
        if(len_untracked): status_str += "{0}({1}) ".format(BR(GIT_STATUS_UNTRACKED),  len_untracked );


        repo_pretty_name = colorize_repo_name(git_repo);
        output = "{0}/{1} {2}".format(
            repo_pretty_name,
            git_repo.current_branch.name,
            status_str
        );

        print(output);


main();
