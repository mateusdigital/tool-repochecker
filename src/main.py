#!/usr/bin/env python3
import os;
import os.path;
import glob;
import shlex;
import subprocess;
from pathlib import Path;
import pdb;

GIT_STATUS_MODIFIED  = "M";
GIT_STATUS_ADDED     = "A";
GIT_STATUS_DELETED   = "D";
GIT_STATUS_RENAMED   = "R";
GIT_STATUS_COPIED    = "C";
GIT_STATUS_UPDATED   = "U";

def log_debug(fmt, *args):
    formatted = fmt.format(*args);
    print(formatted);

def log_info(fmt, *args):
    # pdb.set_trace();
    formatted = fmt.format(*args);
    print(formatted);


def get_home_path():
    return os.path.abspath(os.path.expanduser("~"));

def git_exec(path, args):
    cmd = "git -C \"%s\" %s" % (path, args);
    cmd_components = shlex.split(cmd);
    log_debug("[git_exec] {0}", cmd);

    p = subprocess.Popen(cmd_components, stdout=subprocess.PIPE, stderr=subprocess.PIPE);
    output, errors = p.communicate()
    if p.returncode:
        print('Failed running %s' % cmd);
        # raise Exception(errors)

    return output.decode('utf-8');

def clean_branch_name(branch_name):
    clean_name = branch_name.strip(" ").strip("*").strip(" ");
    return clean_name;

def is_current_branch(branch_name):
    clean_name = branch_name.strip(" ");
    return clean_name.startswith("*");


class GitBranch:
    def __init__(self, branch_name, repo):
        self.name       = clean_branch_name(branch_name);
        self.is_current = is_current_branch(branch_name);
        self.repo       = repo;

        self.is_dirty = False;
        self.modified = [];
        self.added    = [];
        self.deleted  = [];
        self.renamed  = [];
        self.copied   = [];
        self.updated  = [];

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

class GitRepo:
    def __init__(self, root_path):
        self.root_path      = root_path;
        self.branches       = [];
        self.current_branch = None;
        self.is_dirty       = False;

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
    start_path = os.path.join(
        get_home_path(),
        "Documents/Projects/stdmatt/"
    );

    ##
    ## Discover the repositories.
    git_repos = [];
    for git_path in Path(start_path).rglob(".git"):
        git_root_path = os.path.dirname(git_path);

        git_repo = GitRepo(git_root_path);
        git_repos.append(git_repo);

    ##
    ## Update the Repositories.
    log_info("Found {0} repos...", len(git_repos));
    repos_to_show = [];
    for i in range(0, len(git_repos)):
        log_info("Updating Repositiory ({0} of {1})", i+1, len(git_repos));

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
        len_modified = len(branch.modified);
        len_added    = len(branch.added   );
        len_deleted  = len(branch.deleted );
        len_renamed  = len(branch.renamed );
        len_copied   = len(branch.copied  );
        len_updated  = len(branch.updated );

        status_str = "";
        if(len_modified): status_str += "{0}({1}) ".format(GIT_STATUS_MODIFIED, len_modified);
        if(len_added   ): status_str += "{0}({1}) ".format(GIT_STATUS_ADDED,    len_added   );
        if(len_deleted ): status_str += "{0}({1}) ".format(GIT_STATUS_DELETED,  len_deleted );
        if(len_renamed ): status_str += "{0}({1}) ".format(GIT_STATUS_RENAMED,  len_renamed );
        if(len_copied  ): status_str += "{0}({1}) ".format(GIT_STATUS_COPIED,   len_copied  );
        if(len_updated ): status_str += "{0}({1}) ".format(GIT_STATUS_UPDATED,  len_updated );

        output = "{0}/{1} {2}".format(
            os.path.basename(git_repo.root_path),
            git_repo.current_branch.name,
            status_str
        );

        print(output);


main();
