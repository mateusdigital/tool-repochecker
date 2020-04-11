#!/usr/bin/env python3
##~---------------------------------------------------------------------------##
##                        _      _                 _   _                      ##
##                    ___| |_ __| |_ __ ___   __ _| |_| |_                    ##
##                   / __| __/ _` | '_ ` _ \ / _` | __| __|                   ##
##                   \__ \ || (_| | | | | | | (_| | |_| |_                    ##
##                   |___/\__\__,_|_| |_| |_|\__,_|\__|\__|                   ##
##                                                                            ##
##  File      : repochecker.py                                                ##
##  Project   : repochecker                                                   ##
##  Date      : Feb 12, 2020                                                  ##
##  License   : GPLv3                                                         ##
##  Author    : stdmatt <stdmatt@pixelwizards.io>                             ##
##  Copyright : stdmatt - 2020                                                ##
##                                                                            ##
##  Description :                                                             ##
##                                                                            ##
##---------------------------------------------------------------------------~##

import os;
import os.path;
import glob;
import shlex;
import subprocess;
import sys;
import pdb;
import argparse;

from pathlib import Path;
from .colors import *;
from .colors import colors

##----------------------------------------------------------------------------##
## Info                                                                       ##
##----------------------------------------------------------------------------##
__version__   = "0.0.0";
__author__    = "stdmatt - <stdmatt@pixelwizards.io>";
__date__      = "Apr 09, 2020";
__copyright__ = "Copyright 2020 - stdmatt";
__license__   = 'GPLv3';


##----------------------------------------------------------------------------##
## Constants                                                                  ##
##----------------------------------------------------------------------------##
GIT_STATUS_MODIFIED  = "M";
GIT_STATUS_ADDED     = "A";
GIT_STATUS_DELETED   = "D"
GIT_STATUS_RENAMED   = "R";
GIT_STATUS_COPIED    = "C";
GIT_STATUS_UPDATED   = "U";
GIT_STATUS_UNTRACKED = "??";

PROGRAM_NAME      = "repochecker";
PROGRAM_COPYRIGHT =  2020;


##----------------------------------------------------------------------------##
## Globals                                                                    ##
##----------------------------------------------------------------------------##
class Globals:
    ##
    ## Command Line Args.
    update_remotes = False;
    auto_pull      = False;

    submodules = False;

    is_debug  = False;
    show_push = False;
    show_pull = False;

    start_path = "";

    ##
    ## Housekeeping.
    tab_size = -1;


##----------------------------------------------------------------------------##
## Log Functions                                                              ##
##----------------------------------------------------------------------------##
##------------------------------------------------------------------------------
def get_help_str():
    return """Usage:
  {program_name} [--help] [--version]
  {program_name} [--debug] [--no-colors]
  {program_name} [--remote] [--auto-pull]
  {program_name} [--submodules]
  {program_name} [--show-push] [--show-pull]
  {program_name} <start-path>

Options:
  *-h --help     : Show this screen.
  *-v --version  : Show program version and copyright.

Notes:
  <start-path> if not given is assumed to be the current working directory.

  Options marked with * are exclusive, i.e. the {program_name} will run that
  and exit after the operation.""".format(
      program_name=PROGRAM_NAME
  );

##------------------------------------------------------------------------------
def show_help():
    print(get_help_str());
    exit(0);

##------------------------------------------------------------------------------
def show_version():
    msg = """
{program_name} - {version} - stdmatt <stdmatt@pixelwizards.io>
Copyright (c) {copyright} - stdmatt
This is a free software (GPLv3) - Share/Hack it
Check http://stdmatt.com for more :)""".format(
        program_name=PROGRAM_NAME,
        version=__version__,
        copyright=PROGRAM_COPYRIGHT
    );
    print(msg);
    exit(0);


##----------------------------------------------------------------------------##
## Log Functions                                                              ##
##----------------------------------------------------------------------------##
##------------------------------------------------------------------------------
def log_debug(fmt, *args):
    if(not Globals.is_debug):
        return;

    formatted = fmt.format(*args);
    print(colors.green("[DEBUG]"), formatted);

##------------------------------------------------------------------------------
def log_debug_error(fmt, *args):
    if(not Globals.is_debug):
        return;

    formatted = fmt.format(*args);
    print("[DEBUG-ERROR] ", formatted);

##------------------------------------------------------------------------------
def log_error(fmt, *args):
    formatted = fmt.format(*args);
    print(colors.red("[ERROR]"), formatted);

##------------------------------------------------------------------------------
def log_info(fmt, *args):
    # pdb.set_trace();
    formatted = fmt.format(*args);
    print(colors.blue("[INFO]"), formatted);

##------------------------------------------------------------------------------
def log_fatal(fmt, *args):
    if(len(args) != 0):
        formatted = fmt.format(*args);
    else:
        formatted = fmt;

    print(colors.red("[FATAL]"), formatted);
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
    log_debug("{0}", cmd);

    p = subprocess.Popen(cmd_components, stdout=subprocess.PIPE, stderr=subprocess.PIPE);
    output, errors = p.communicate();

    if(p.returncode):
        log_debug_error("Failed running {0}", cmd);
        return errors.decode('utf-8'), p.returncode;

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

        self.modified  = [];
        self.added     = [];
        self.deleted   = [];
        self.renamed   = [];
        self.copied    = [];
        self.updated   = [];
        self.untracked = [];

        self.diffs_to_pull = [];
        self.diffs_to_push = [];

    def is_dirty(self):
        return self.is_local_dirty() or self.is_remote_dirty();

    def is_local_dirty(self):
        return len(self.modified ) != 0 or len(self.added    ) != 0 or \
               len(self.deleted  ) != 0 or len(self.renamed  ) != 0 or \
               len(self.copied   ) != 0 or len(self.updated  ) != 0 or \
               len(self.untracked) != 0;

    def is_remote_dirty(self):
        return (len(self.diffs_to_pull) != 0 and Globals.show_pull) \
            or (len(self.diffs_to_push) != 0 and Globals.show_push);

    ##--------------------------------------------------------------------------
    def check_status(self):
        ##
        ## Find the local modifications.
        if(self.is_current):
            status_result, error_code = git_exec(self.repo.root_path, "status -suno");
            ## @todo(stdmatt): error handling...
            for line in status_result.split("\n"):
                if(len(line) == 0 or not self.is_current):
                    continue;

                path     = line[2: ].strip(" ");
                status   = line[0:2].strip(" ");
                status_x = status[0];

                if(status_x == GIT_STATUS_MODIFIED):
                    self.modified.append(path);
                elif(status_x == GIT_STATUS_ADDED):
                    self.added.append(path);
                elif(status_x == GIT_STATUS_DELETED):
                    self.deleted.append(path);
                elif(status_x == GIT_STATUS_RENAMED):
                    self.renamed.append(path);
                elif(status_x == GIT_STATUS_COPIED):
                    self.copied.append(path);
                elif(status_x == GIT_STATUS_UPDATED):
                    self.updated.append(path);
                elif(status_x == GIT_STATUS_UNTRACKED):
                    self.untracked.append(path);

        ##
        ## Find the differences to remote.
        ## @TODO(stdmatt): I'm just checking for origin right now that's my
        ## main use case... I need to understand better how to check for
        ## other remotes as well.
        remote_name = "origin";

        self.diffs_to_pull = self.find_diffs_from_remote("{1}..{0}/{1}", remote_name);
        self.diffs_to_push = self.find_diffs_from_remote("{0}/{1}..{1}", remote_name);


    ##--------------------------------------------------------------------------
    def try_to_pull(self):
        color_repo_name   = colors.pulling_repo_name  (self.repo.name);
        color_branch_name = colors.pulling_branch_name(self.name);

        if(not self.is_current):
            log_error(
                "{0}/{1} is not the current branch and will not be auto pulled.",
                color_repo_name,
                color_branch_name
            );

        if(self.is_local_dirty()):
            log_info(
                "{0}/{1} is dirty and will not be auto pulled.",
                color_repo_name,
                color_branch_name
            );
            return;

        if(len(self.diffs_to_pull) == 0):
            return;

        log_info("{0}/{1} is being auto pulled.", color_repo_name, color_branch_name);

        output, return_code = git_exec(self.repo.root_path, "pull origin {0}".format(self.name))
        if(return_code != 0):
            log_error(
                "{0}/{1} had an error on auto pull!!\nError: {2}\n\nRolling back...",
                color_repo_name,
                color_branch_name,
                output
            );

            output, return_code = git_exec(self.repo.root_path, "reset --merge");
            if(return_code != 0):
                log_fatal(
                    "{0}/{1} had an error when rolling back\nError: {2}",
                    color_repo_name,
                    color_branch_name,
                    output
                );

        self.diffs_to_pull = [];

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
        log_debug(
            "Found {2} Path:({0}) - Submodule: ({1})",
            colors.path(root_path),
            is_submodule,
            "Submodule" if is_submodule else "Repo"
        );

        self.name           = os.path.basename(root_path);
        self.root_path      = root_path;
        self.is_submodule   = is_submodule;
        self.branches       = [];
        self.current_branch = None;
        self.submodules     = [];

        if(Globals.submodules):
            self.find_submodules();

    ##--------------------------------------------------------------------------
    def is_dirty(self):
        for branch in self.branches:
            if(branch.is_dirty()):
                return True;

        for submodule in self.submodules:
            if(submodule.is_dirty()):
                return True;

        return False;

    ##--------------------------------------------------------------------------
    def update_remotes(self):
        if(Globals.update_remotes):
            log_debug("Updating remotes...");
            git_exec(self.root_path, "remote update")

        for submodule in self.submodules:
            submodule.update_remotes();

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

        for submodule in self.submodules:
            submodule.check_status();

    ##--------------------------------------------------------------------------
    def try_to_pull(self):
        if(self.current_branch is None):
            log_debug(
                "Repo ({0}) doesn't have a current branch",
                 self.root_path
            );
            return;

        ## @NOTICE(stdmatt): Right now we're just pulling the current branch
        ## we need to research how to pull different branches...
        self.current_branch.try_to_pull();

        for submodule in self.submodules:
            submodule.try_to_pull()

    ##--------------------------------------------------------------------------
    def print_result(self):
        if(not self.is_dirty()):
            return;

        tab_indent();

        repo_pretty_name = colors.colorize_repo_name(self);
        tab_print(repo_pretty_name);

        for branch in self.branches:
            if(not branch.is_dirty()):
                continue;

            if(branch is None):
                pdb.set_trace();

            def _concat_status_str(diff, color_func, msg):
                if (len(diff) == 0):
                    return "";
                return "{0}({1}) ".format(color_func(msg), color_func(len(diff)));

            def _print_branch_name(branch_name, status_str):
                branch_name = colors.branch_name(branch_name);
                if(len(status_str) != 0):
                    tab_print("{0} - {1}".format(branch_name, status_str));
                else:
                    tab_print("{0}".format(branch_name));

            def _print_push_pull_info(diff, msg):
                if(len(diff) == 0):
                    return;

                tab_indent();
                tab_print("{0}: ({1})".format(msg, colors.number(len(diff))));

                for line in diff:
                    tab_indent();

                    components = line.split(" ");
                    sha = colors.commit_sha(components[0]);
                    msg = colors.commit_msg(" ".join(components[1:]));

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

            status_str += _concat_status_str(branch.modified  , colors.branch_modified  ,  GIT_STATUS_MODIFIED );
            status_str += _concat_status_str(branch.added     , colors.branch_added     ,  GIT_STATUS_ADDED    );
            status_str += _concat_status_str(branch.deleted   , colors.branch_deleted   ,  GIT_STATUS_DELETED  );
            status_str += _concat_status_str(branch.renamed   , colors.branch_renamed   ,  GIT_STATUS_RENAMED  );
            status_str += _concat_status_str(branch.copied    , colors.branch_copied    ,  GIT_STATUS_COPIED   );
            status_str += _concat_status_str(branch.updated   , colors.branch_updated   ,  GIT_STATUS_UPDATED  );
            status_str += _concat_status_str(branch.untracked , colors.branch_untracked ,  GIT_STATUS_UNTRACKED);

            tab_indent();
            _print_branch_name(branch.name, status_str);

            if(Globals.show_push):
                _print_push_pull_info(branch.diffs_to_push, colors.diffs_to_push("To Push"));
            if(Globals.show_pull):
                _print_push_pull_info(branch.diffs_to_pull, colors.diffs_to_pull("To Pull"));

            tab_unindent();

        for submodule in self.submodules:
            submodule.print_result();
        tab_unindent();

##------------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="git repository checker",
        usage=get_help_str(),
        add_help=False
    );

    ## Help / Version.
    parser.add_argument("--help",    dest="show_help",    action="store_true", default=False);
    parser.add_argument("--version", dest="show_version", action="store_true", default=False);

    ## Remote.
    parser.add_argument("--remote",    dest="update_remote", action="store_true", default=False);
    parser.add_argument("--auto-pull", dest="auto_pull",     action="store_true", default=False);

    ## Submodules.
    parser.add_argument("--submodules", dest="submodules", action="store_true", default=False);

    ## Output.
    parser.add_argument("--debug",     dest="is_debug",      action="store_true",  default=False);
    parser.add_argument("--no-colors", dest="color_enabled", action="store_false", default=True );
    parser.add_argument("--show-push", dest="show_push",     action="store_true",  default=False);
    parser.add_argument("--show-pull", dest="show_pull",     action="store_true",  default=False);


    ## Start Path.
    parser.add_argument(
        "path",
        default=os.getcwd(),
        nargs="?"
    );

    return parser.parse_args();


##----------------------------------------------------------------------------##
## Entry Point                                                                ##
##----------------------------------------------------------------------------##
def run():
    ##
    ## Parse the command line arguments.
    args = parse_args();

    ## Help / Version.
    if(args.show_help):
        show_help();
    if(args.show_version):
        show_version();

    ## Remote.
    Globals.update_remotes = args.update_remote;
    Globals.auto_pull      = args.auto_pull;

    ## Submodules.
    Globals.submodules = args.submodules;

    ## Output
    if(not args.color_enabled):
        colors.disable_coloring();

    Globals.is_debug  = args.is_debug or True;
    Globals.show_pull = args.show_pull;
    Globals.show_push = args.show_push;

    Globals.start_path = normalize_path(args.path);
    Globals.start_path = normalize_path("~/Documents/Projects/stdmatt/personal/license_header")

    ##
    ## Discover the repositories.
    git_repos = [];
    for root, dirs, files in os.walk(Globals.start_path):
        if(".git" not in dirs):
            continue;

        git_repo = GitRepo(root);
        git_repos.append(git_repo);

        del dirs[0:];


    ##
    ## Update the Repositories.
    log_info("Found {0} repos...", len(git_repos));

    for i in range(0, len(git_repos)):
        log_debug("Updating Repository ({0} of {1})", i+1, len(git_repos));

        git_repo = git_repos[i];

        git_repo.update_remotes();
        git_repo.find_branches ();
        git_repo.check_status  ();

        if(Globals.auto_pull):
            git_repo.try_to_pull();

    ##
    ## Present Repositories.
    for i in range(0, len(git_repos)):
        git_repo = git_repos[i];
        git_repo.print_result();
