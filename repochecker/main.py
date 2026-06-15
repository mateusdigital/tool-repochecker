#!/usr/bin/env python3
##~---------------------------------------------------------------------------##
##                               *       +                                    ##
##                         '                  |                               ##
##                     ()    .-.,="``"=.    - o -                             ##
##                           '=/_       \     |                               ##
##                        *   |  '=._    |                                    ##
##                             \     `=./`,        '                          ##
##                          .   '=.__.=' `='      *                           ##
##                 +                         +                                ##
##                      O      *        '       .                             ##
##                                                                            ##
##  File      : main.py                                                       ##
##  Project   : repochecker                                                   ##
##  Date      : Feb 12, 2020                                                  ##
##  License   : See project's COPYING.TXT for full info.                      ##
##  Author    : mateus.digital <hello@mateus.digital>                         ##
##  Copyright : mateus.digital - 2020, 2022, 2024                             ##
##                                                                            ##
##  Description :                                                             ##
##                                                                            ##
##---------------------------------------------------------------------------~##

##----------------------------------------------------------------------------##
## Imports                                                                    ##
##----------------------------------------------------------------------------##
import os;
import os.path;
import json;
import shlex;
import subprocess;
import sys;
import pdb;
import argparse;
import threading;
import signal;


##----------------------------------------------------------------------------##
## Info                                                                       ##
##----------------------------------------------------------------------------##
PROGRAM_NAME            = "repochecker";
PROGRAM_VERSION         = "3.1.0";
PROGRAM_BUILD           = 0;
PROGRAM_AUTHOR          = "Saturno Software";
PROGRAM_EMAIL           = "hello@saturno.software";
PROGRAM_WEBSITE         = "https://saturno.software";
PROGRAM_COPYRIGHT_OWNER = "Saturno Software";
PROGRAM_COPYRIGHT_YEARS = "2020, 2021, 2024, 2026";
PROGRAM_DATE            = "09 April 2020";
PROGRAM_LICENSE         = "GPLv3";

_DIR = os.path.dirname(os.path.abspath(__file__));
REPO_ROOT = os.path.normpath(os.path.join(_DIR, ".."));
PACKAGE_JSON_PATH = os.path.join(REPO_ROOT, "package.json");

def _load_package_json():
    try:
        with open(PACKAGE_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f);
    except (OSError, ValueError):
        return {};

_PKG = _load_package_json();
PROGRAM_NAME = _PKG.get("name", PROGRAM_NAME);
PROGRAM_VERSION = _PKG.get("version", PROGRAM_VERSION);
PROGRAM_BUILD = int(_PKG.get("build", PROGRAM_BUILD));
PROGRAM_LICENSE = _PKG.get("license", PROGRAM_LICENSE);

SATURNO_PLATFORM_ROOT = os.path.join(os.path.expanduser("~"), ".saturnosoftware");
SATURNO_HOME_DIR = os.path.join(SATURNO_PLATFORM_ROOT, PROGRAM_NAME);
SATURNO_BIN_DIR = os.path.join(SATURNO_HOME_DIR, "bin");
SATURNO_CONFIG_DIR = os.path.join(SATURNO_HOME_DIR, "config");
SATURNO_DATA_DIR = os.path.join(SATURNO_HOME_DIR, "data");

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

NL                   = "\n";

GLOBAL_REPOCHECKER_IGNORE_DIRPATH  = os.path.abspath(os.path.expanduser("~"));
GLOBAL_REPOCHECKER_IGNORE_FULLPATH = os.path.join(GLOBAL_REPOCHECKER_IGNORE_DIRPATH, ".repochecker_ignore");


##----------------------------------------------------------------------------##
## Globals                                                                    ##
##----------------------------------------------------------------------------##
class Globals:
    ##
    ## Command Line Args.
    update_remotes = False;
    auto_pull      = False;
    force_pull     = False;

    submodules = False;

    is_debug     = True;
    is_debug_git = False;
    show_push    = False;
    show_pull    = False;
    show_short   = False;

    no_colors    = False;

    start_path = "";

    ##
    ## Housekeeping.
    tab_size              = -1;
    directories_to_ignore = [];


##----------------------------------------------------------------------------##
## Color Functions                                                            ##
##----------------------------------------------------------------------------##
class NullTermColor:
    GREEN   = 0;
    RED     = 0;
    BLUE    = 0;
    YELLOW  = 0;
    WHITE   = 0;
    MAGENTA = 0;
    CYAN    = 0;
    GREY    = 0;
    ON_RED  = 0;

    def colored(text, _ = None, __ = None):
        return text;

termcolor = NullTermColor;
## @todo(stdmatt): Try to import the termcolor... 3/16/2021, 10:46:29 AM


##------------------------------------------------------------------------------
def colors_green  (s): return termcolor.colored(s, termcolor.GREEN  );
def colors_red    (s): return termcolor.colored(s, termcolor.RED    );
def colors_blue   (s): return termcolor.colored(s, termcolor.BLUE   );
def colors_yellow (s): return termcolor.colored(s, termcolor.YELLOW );
def colors_white  (s): return termcolor.colored(s, termcolor.WHITE  );
def colors_magenta(s): return termcolor.colored(s, termcolor.MAGENTA);
def colors_cyan   (s): return termcolor.colored(s, termcolor.CYAN   );
def colors_grey   (s): return termcolor.colored(s, termcolor.GREY   );
def colors_on_red (s): return termcolor.colored(s, fg=None, bg=termcolor.ON_RED);
##------------------------------------------------------------------------------
def colors_number(n): return colors_cyan   (n);
def colors_path  (p): return colors_magenta(p);
##------------------------------------------------------------------------------
def colors_repo_name (name): return colors_magenta(name);
def colors_repo_clean(name): return colors_green  (name);
def colors_repo_dirty(name): return colors_red    (name);

def colors_colorize_git_repo_name(git_repo):
    pretty_name = os.path.basename(git_repo.root_path);
    if(git_repo.is_dirty()):
        pretty_name = colors_repo_dirty(pretty_name);
    else:
        pretty_name = colors_repo_clean(pretty_name);

    prefix = "[Submodule]" if git_repo.is_submodule else "[Repo]";
    path   = git_repo.root_path;

    return "{0} {1} ".format(prefix, pretty_name, path);

##------------------------------------------------------------------------------
def colors_branch_name     (s): return colors_grey  (s);
def colors_branch_modified (s): return colors_yellow(s);
def colors_branch_added    (s): return colors_green (s);
def colors_branch_deleted  (s): return colors_red   (s);
def colors_branch_renamed  (s): return colors_yellow(s);
def colors_branch_copied   (s): return colors_yellow(s);
def colors_branch_updated  (s): return colors_yellow(s);
def colors_branch_untracked(s): return colors_on_red(s);
##------------------------------------------------------------------------------
def colors_diffs_to_pull(s): return colors_yellow(s);
def colors_diffs_to_push(s): return colors_green (s);
##------------------------------------------------------------------------------
def colors_pulling_repo_name  (s): return colors_magenta(s);
def colors_pulling_branch_name(s): return colors_cyan   (s);
##------------------------------------------------------------------------------
def colors_commit_sha(s): return colors_red  (s);
def colors_commit_msg(s): return colors_white(s);


##----------------------------------------------------------------------------##
## Log Functions                                                              ##
##----------------------------------------------------------------------------##
##------------------------------------------------------------------------------
def get_help_str():
    return """Usage:
  {program_name} [--help] [--version]
  {program_name} [--debug] [--no-colors]
  {program_name} [--remote] [--auto-pull] [--force-pull]
  {program_name} [--submodules]
  {program_name} [--show-push] [--show-pull] [--show-all]
  {program_name} [--short]
  {program_name} [-Json | --json]
  {program_name} [<start-path>]

  --debug      : Prints extra information about the program execution.
  --no-colors  : Disables coloring the output.

  --remote     : Fetches the status of the repo's remotes (slow).
  --submodules : Makes the operations applies to submodules as well.

  --show-push  : Shows the information about changes to push.
  --show-pull  : Shows the information about changes to pull.
  --show-all   : Implies --show-push and --show-pull.

  --short      : Displays the information into a condensed format.

  --auto-pull   : Automatically pull changes from remote if the branch is
                  clean and is the current branch.
  
  --force-pull  : Forces pulling changes from remote even if the branch is
                  dirty or is not the current branch.  
Options:
  *-h --help     : Show this screen.
  *-v --version  : Show program version and copyright.
  *-Json --json  : Print structured CLI metadata for help/version consumers.

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
    print(get_version_text());
    exit(0);

##------------------------------------------------------------------------------
def get_version_text():
    msg = """{program_name} - {program_version}-{program_build} - {program_author} <{program_email}>
Copyright (c) {program_copyright_years} - {program_copyright_owner}
This is a free software ({program_license}) - Share/Hack it
Check {program_website} for more :)""".format(
        program_name=PROGRAM_NAME,
        program_version=PROGRAM_VERSION,
        program_build=PROGRAM_BUILD,
        program_author=PROGRAM_AUTHOR,
        program_email=PROGRAM_EMAIL,
        program_copyright_years=PROGRAM_COPYRIGHT_YEARS,
        program_copyright_owner=PROGRAM_COPYRIGHT_OWNER,
        program_license=PROGRAM_LICENSE,
        program_website=PROGRAM_WEBSITE,
    );
    return msg;

##------------------------------------------------------------------------------
def cli_path(path):
    return normalize_path(path);

##------------------------------------------------------------------------------
def get_cli_commands():
    return [
        { "Name": "scan", "Description": "Scan repositories under the selected path and print pending local or remote work", "SupportsJsonOutput": False },
        { "Name": "remote", "Description": "Fetch remote state before scanning", "SupportsJsonOutput": False },
        { "Name": "auto-pull", "Description": "Pull clean current branches with pending remote changes", "SupportsJsonOutput": False },
        { "Name": "force-pull", "Description": "Discard local changes and pull current branches with pending remote changes", "SupportsJsonOutput": False },
        { "Name": "submodules", "Description": "Include repository submodules in scan and pull operations", "SupportsJsonOutput": False },
        { "Name": "show-push", "Description": "Show commits waiting to be pushed", "SupportsJsonOutput": False },
        { "Name": "show-pull", "Description": "Show commits waiting to be pulled", "SupportsJsonOutput": False },
        { "Name": "short", "Description": "Print condensed repository status output", "SupportsJsonOutput": False },
    ];

##------------------------------------------------------------------------------
def get_cli_metadata():
    return {
        "Schema"      : "saturno-cli-metadata/v1",
        "Name"        : PROGRAM_NAME,
        "Summary"     : "CLI tool for checking many Git repositories and submodules from one command.",
        "Version"     : PROGRAM_VERSION,
        "Build"       : PROGRAM_BUILD,
        "Author"      : PROGRAM_AUTHOR,
        "Email"       : PROGRAM_EMAIL,
        "Website"     : PROGRAM_WEBSITE,
        "License"     : PROGRAM_LICENSE,
        "UsageText"   : get_help_str(),
        "VersionText" : get_version_text(),
        "Texts"       : {
            "Usage"   : get_help_str(),
            "Version" : get_version_text(),
        },
        "OutputModes" : ["text", "json"],
        "Commands"    : get_cli_commands(),
        "Paths"       : {
            "PlatformRoot" : cli_path(SATURNO_PLATFORM_ROOT),
            "InstallRoot"  : cli_path(SATURNO_HOME_DIR),
            "BinDir"       : cli_path(SATURNO_BIN_DIR),
            "ConfigRoot"   : cli_path(SATURNO_CONFIG_DIR),
            "DataRoot"     : cli_path(SATURNO_DATA_DIR),
        },
        "Supports"    : {
            "JsonMetadata" : True,
            "JsonCommands" : [],
            "JsonErrors"   : True,
            "ChangesDirectory" : False,
        },
    };

##------------------------------------------------------------------------------
def print_json_metadata():
    print(json.dumps(get_cli_metadata(), indent=2));
    exit(0);

##------------------------------------------------------------------------------
def print_json_error(code, message, command=None):
    payload = {
        "Schema"  : "saturno-cli-error/v1",
        "Tool"    : PROGRAM_NAME,
        "Command" : command,
        "Code"    : code,
        "Message" : message,
    };
    print(json.dumps(payload), file=sys.stderr);
    exit(1);


##----------------------------------------------------------------------------##
## Log Functions                                                              ##
##----------------------------------------------------------------------------##
##------------------------------------------------------------------------------
def repo_or_sub(git_repo):
    return "Submodule" if git_repo.is_submodule else "Repo";

##------------------------------------------------------------------------------
def build_full_repo_name(git_repo):
    name = git_repo.name;
    repo = git_repo;
    while(repo.parent is not None):
        name = "{}/{}".format(repo.parent.name, name);
        repo = repo.parent;
    return name;

##------------------------------------------------------------------------------
def log_debug(fmt, *args):
    if(not Globals.is_debug):
        return;
    formatted = fmt.format(*args);
    print(colors_green("[DEBUG]"), formatted);

##------------------------------------------------------------------------------
def log_git(fmt, *args):
    if(not Globals.is_debug_git):
        return;
    formatted = fmt.format(*args);
    print(colors_magenta("[GIT]"), formatted);

##------------------------------------------------------------------------------
def log_git_error(fmt, *args):
    if(not Globals.is_debug_git):
        return;
    formatted = fmt.format(*args);
    print(colors_red("[GIT-ERROR]"), formatted);

##------------------------------------------------------------------------------
def log_error(fmt, *args):
    formatted = fmt.format(*args);
    print(colors_red("[ERROR]"), formatted);

##------------------------------------------------------------------------------
def log_info(fmt, *args):
    # pdb.set_trace();
    formatted = fmt.format(*args);
    print(colors_blue("[INFO]"), formatted);

##------------------------------------------------------------------------------
def log_warn(fmt, *args):
    # pdb.set_trace();
    formatted = fmt.format(*args);
    print(colors_yellow("[WARN]"), formatted);

##------------------------------------------------------------------------------
def log_fatal(fmt, *args):
    if(len(args) != 0):
        formatted = fmt.format(*args);
    else:
        formatted = fmt;

    print(colors_red("[FATAL]"), formatted);
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
def tabs():
    spacing_size = 2;
    spacing_char = " ";
    spacing      = spacing_char * spacing_size;
    ret          = "";

    if(Globals.tab_size > 0):
        ret = (spacing * Globals.tab_size);
    return ret;


##----------------------------------------------------------------------------##
## OS / Path Functions                                                        ##
##----------------------------------------------------------------------------##
##------------------------------------------------------------------------------
def get_home_path():
    return os.path.abspath(os.path.expanduser("~"));

##------------------------------------------------------------------------------
def normalize_path(path):
    path = path.replace("\\", "/");
    path = os.path.expanduser(path);
    path = os.path.normcase  (path);
    path = os.path.normpath  (path);
    path = os.path.abspath   (path);
    return path;

##------------------------------------------------------------------------------
def has_git_repo_marker(dir_entries, file_entries):
    return ".git" in dir_entries or ".git" in file_entries;


##----------------------------------------------------------------------------##
## Git Functions                                                              ##
##----------------------------------------------------------------------------##
##------------------------------------------------------------------------------
def decode_git_output(data):
    return data.decode("utf-8", errors="replace");

##------------------------------------------------------------------------------
def git_exec(path, args):
    path           = normalize_path(path);
    cmd            = "git -C \"%s\" %s" % (path, args);
    cmd_components = ["git", "-C", path] + shlex.split(args);
    log_git("{0}", cmd);

    try:
        p = subprocess.Popen(cmd_components, stdout=subprocess.PIPE, stderr=subprocess.PIPE);
        output, errors = p.communicate();
    except OSError as ex:
        log_git_error("Failed running {0}: {1}", cmd, ex);
        return str(ex), 1;

    if(p.returncode):
        log_git_error("Failed running {0}", cmd);
        return decode_git_output(errors), p.returncode;

    return decode_git_output(output), p.returncode;

##------------------------------------------------------------------------------
def git_clean_branch_name(branch_name):
    clean_name = branch_name.strip(" ").strip("*").strip(" ");
    return clean_name;

##------------------------------------------------------------------------------
def git_is_current_branch(branch_name):
    clean_name = branch_name.strip(" ");
    return clean_name.startswith("*");

##------------------------------------------------------------------------------
def git_is_detached_branch(branch_name):
    clean_name = branch_name.strip(" ");
    return clean_name.startswith("HEAD detached at");

##----------------------------------------------------------------------------##
## Types                                                                      ##
##----------------------------------------------------------------------------##
##------------------------------------------------------------------------------
class GitBranch:
    ##--------------------------------------------------------------------------
    def __init__(self, branch_name, repo):
        self.name        = git_clean_branch_name (branch_name);
        self.is_current  = git_is_current_branch (branch_name);
        self.is_detached = git_is_detached_branch(branch_name);
        self.repo        = repo;

        self.modified  = [];
        self.added     = [];
        self.deleted   = [];
        self.renamed   = [];
        self.copied    = [];
        self.updated   = [];
        self.untracked = [];

        self.diffs_to_pull = [];
        self.diffs_to_push = [];

        log_debug(
            "Creating Branch\n" +
            "   Name : {}   \n" +
            "   Owner: {}   \n" +
            "   State: {}     ",
            self.name,
            build_full_repo_name(self.repo),
            "Detached" if self.is_detached else "Current" if self.is_current else "None",
        );

    ##--------------------------------------------------------------------------
    def is_dirty(self):
        return self.is_local_dirty() or self.is_remote_dirty();

    ##--------------------------------------------------------------------------
    def is_local_dirty(self):
        return len(self.modified ) != 0 or len(self.added    ) != 0 or \
               len(self.deleted  ) != 0 or len(self.renamed  ) != 0 or \
               len(self.copied   ) != 0 or len(self.updated  ) != 0 or \
               len(self.untracked) != 0;

    ##--------------------------------------------------------------------------
    def is_remote_dirty(self):
        return (len(self.diffs_to_pull) != 0 and Globals.show_pull) \
            or (len(self.diffs_to_push) != 0 and Globals.show_push);

    ##--------------------------------------------------------------------------
    def check_status(self):
        ##
        ## Find the local modifications.
        if(self.is_current):
            status_result, error_code = git_exec(self.repo.root_path, "status -suno");
            if(error_code != 0):
                log_error(
                    "{} {} - Failed to get branch status for ({}) - Error Code: ({}) - Result: ({})",
                    repo_or_sub(self.repo),
                    self.repo.name,
                    self.name,
                    error_code,
                    status_result.strip()
                );
                return;

            for line in status_result.split("\n"):
                if(len(line) == 0 or not self.is_current):
                    continue;
                if(len(line) < 3):
                    continue;

                path     = line[2: ].strip(" ");
                status   = line[0:2].strip(" ");
                if(len(status) == 0):
                    continue;
                if(status == GIT_STATUS_UNTRACKED):
                    self.untracked.append(path);
                    continue;
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

        ##
        ## Find the differences to remote.
        ## @TODO(stdmatt): I'm just checking for origin right now that's my
        ## main use case... I need to understand better how to check for
        ## other remotes as well.
        remote_name = "origin";

        self.diffs_to_pull = self.find_diffs_from_remote("{1}..{0}/{1}", remote_name);
        self.diffs_to_push = self.find_diffs_from_remote("{0}/{1}..{1}", remote_name);

        if(len(self.diffs_to_pull) != 0):
            log_debug(
                "{} {}/{} diffs to pull: {}",
                repo_or_sub(self.repo),
                build_full_repo_name(self.repo),
                self.name,
                len(self.diffs_to_pull)
            );
        if(len(self.diffs_to_push) != 0):
            log_debug(
                "{} {}/{} diffs to push: {}",
                repo_or_sub(self.repo),
                build_full_repo_name(self.repo),
                self.name,
                len(self.diffs_to_push)
            );


    ##--------------------------------------------------------------------------
    def try_to_pull(self):
        if(not Globals.auto_pull and not Globals.force_pull):
            return;

        color_repo_name   = colors_pulling_repo_name  (build_full_repo_name(self.repo));
        color_branch_name = colors_pulling_branch_name(self.name);

        ##
        ## Check conditions for auto-pull (not for force-pull)
        if(Globals.auto_pull and not Globals.force_pull):
            if(not self.is_current):
                log_error(
                    "{0}/{1} is not the current branch and will not be auto pulled.",
                    color_repo_name,
                    color_branch_name
                );
                return;
            if(self.is_detached):
                log_error(
                    "{0}/{1} is detached branch and will not be auto pulled.",
                    color_repo_name,
                    color_branch_name
                );
                return;

            if(self.is_local_dirty()):
                log_info(
                    "{0}/{1} is dirty and will not be auto pulled.",
                    color_repo_name,
                    color_branch_name
                );
                return;
        else:
            ##
            ## For force-pull, check if it's detached (can't pull in detached state)
            if(self.is_detached and Globals.force_pull):
                log_error(
                    "{0}/{1} is detached branch and will not be force pulled.",
                    color_repo_name,
                    color_branch_name
                );
                return;

            ##
            ## For force-pull, discard local changes if branch is dirty
            if(self.is_local_dirty() and Globals.force_pull):
                log_info(
                    "{0}/{1} has local changes. Discarding them before force pull...",
                    color_repo_name,
                    color_branch_name
                );
                ##
                ## Clean untracked files first
                output, return_code = git_exec(self.repo.root_path, "clean -fd");
                if(return_code != 0):
                    log_error(
                        "{0}/{1} had an error cleaning untracked files!\nError: {2}",
                        color_repo_name,
                        color_branch_name,
                        output
                    );
                    return;
                ##
                ## Reset to discard staged and unstaged changes
                output, return_code = git_exec(self.repo.root_path, "reset --hard");
                if(return_code != 0):
                    log_error(
                        "{0}/{1} had an error discarding changes!\nError: {2}",
                        color_repo_name,
                        color_branch_name,
                        output
                    );
                    return;

        if(len(self.diffs_to_pull) == 0):
            return;

        if(Globals.force_pull):
            log_info("{0}/{1} is being force pulled.", color_repo_name, color_branch_name);
        else:
            log_info("{0}/{1} is being auto pulled.", color_repo_name, color_branch_name);

        output, return_code = git_exec(self.repo.root_path, "pull origin {0}".format(self.name))
        if(return_code != 0):
            log_error(
                "{0}/{1} had an error on pull!!\nError: {2}\n\nRolling back...",
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
    def __init__(self, root_path, is_submodule=False, parent=None):
        self.name           = os.path.basename(root_path);
        self.root_path      = root_path;
        self.is_submodule   = is_submodule;
        self.parent         = parent;
        self.branches       = [];
        self.current_branch = None;
        self.submodules     = [];

        log_debug(
            "Creating {}   \n" +
            "  Name   : {} \n" +
            "  Parent : {} \n" +
            "  Path   : {}   " ,
            repo_or_sub(self),
            self.name,
            "None" if parent is None else build_full_repo_name(self.parent),
            self.root_path
        );

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
        if(not Globals.update_remotes):
            return;

        log_info("Updating ({}) remotes...", build_full_repo_name(self));
        git_exec(self.root_path, "remote update")

        for submodule in self.submodules:
            submodule.update_remotes();

    ##--------------------------------------------------------------------------
    def find_submodules(self):
        if(not Globals.submodules):
            return;

        result, error_code = git_exec(
            self.root_path,
            "config --file .gitmodules --get-regexp path"
        );

        if(error_code != 0):
            return;

        lines = result.split("\n");
        for line in lines:
            line = line.strip(" ");
            if(len(line) == 0):
                continue;

            components = line.split(None, 1);
            if(len(components) != 2):
                log_error(
                    "Repo {} has an invalid .gitmodules path entry: ({})",
                    build_full_repo_name(self),
                    line
                );
                continue;

            submodule_key  = components[0];
            relative_path  = components[1].strip();
            if(not submodule_key.startswith("submodule.") or not submodule_key.endswith(".path")):
                log_error(
                    "Repo {} has an invalid .gitmodules path key: ({})",
                    build_full_repo_name(self),
                    submodule_key
                );
                continue;

            submodule_name = submodule_key[len("submodule."):-(len(".path"))];
            submodule_path = normalize_path(os.path.join(self.root_path, relative_path));
            log_debug(
                "{}: ({}) found submodule ({}) - Path: ({})",
                repo_or_sub(self),
                self.name,
                submodule_name,
                submodule_path
            );

            if(not os.path.isdir(submodule_path)):
                msg = "\n".join([
                    "While scanning repository submodules"
                    , "repochecker found a submodule entry that doesn't correspond to a valid path."
                    , "   Repository Path        : {0}"
                    , "   Submodule Entry        : {1}"
                    , "   Submodule Invalid Path : {2}"
                ]);
                msg = msg.format(self.root_path, line, submodule_path);
                log_error(msg);
                continue;

            git_repo = GitRepo(submodule_path, True, self);
            self.submodules.append(git_repo);
            git_repo.find_submodules();

    ##--------------------------------------------------------------------------
    def find_branches(self):
        result, error_code = git_exec(self.root_path, "branch");
        if(error_code != 0):
            log_error(
                "{} {} - Failed to get branches - Error Code: ({}) - Result: ({})",
                repo_or_sub(self),
                self.name,
                error_code,
                result
            );
            return;

        lines = result.splitlines();
        for branch_name in lines:
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

    ##------------------------------------------------------------------------------
    def _build_status_str(self, branch):
        def _concat_status_str(diff, color_func, msg):
            if (len(diff) == 0):
                return "";
            return "{0}({1}) ".format(color_func(msg), color_func(len(diff)));

        status_str = "";
        status_str += _concat_status_str(branch.modified  , colors_branch_modified  ,  GIT_STATUS_MODIFIED );
        status_str += _concat_status_str(branch.added     , colors_branch_added     ,  GIT_STATUS_ADDED    );
        status_str += _concat_status_str(branch.deleted   , colors_branch_deleted   ,  GIT_STATUS_DELETED  );
        status_str += _concat_status_str(branch.renamed   , colors_branch_renamed   ,  GIT_STATUS_RENAMED  );
        status_str += _concat_status_str(branch.copied    , colors_branch_copied    ,  GIT_STATUS_COPIED   );
        status_str += _concat_status_str(branch.updated   , colors_branch_updated   ,  GIT_STATUS_UPDATED  );
        status_str += _concat_status_str(branch.untracked , colors_branch_untracked ,  GIT_STATUS_UNTRACKED);
        status_str = status_str.rstrip();

        status_str = " - {0}".format(status_str) if len(status_str) != 0 else "";
        return status_str;

    ##------------------------------------------------------------------------------
    def _build_diffs_str(self, branch):
        ##
        if(Globals.show_short):
            result = "";
            if(Globals.show_pull and len(branch.diffs_to_pull) != 0):
                result += " - {0}:({1})".format(
                    colors_diffs_to_pull("To Pull"),
                    colors_number(len(branch.diffs_to_pull))
                );

            if(Globals.show_push and len(branch.diffs_to_push) != 0):
                result += " - {0}:({1})".format(
                    colors_diffs_to_pull("To Push"),
                    colors_number(len(branch.diffs_to_push))
                );
            return result;

        ##
        ## Long output.
        def _concat_diff(diff):
            if(len(diff) == 0 or Globals.show_short):
                return "";

            output_str = "";
            tab_indent();
            for line in diff:
                components = line.split(" ");
                sha = colors_commit_sha(components[0]);
                msg = colors_commit_msg(" ".join(components[1:]));

                output_str += tabs() + "[{0} {1}]".format(sha, msg) + NL;
            tab_unindent();

            return output_str;

        tab_indent();
        result = NL;

        tab_indent();
        if(Globals.show_pull and len(branch.diffs_to_pull) != 0):
            result += tabs() + "{0}:({1})\n".format(
                colors_diffs_to_pull("To Pull"),
                colors_number(len(branch.diffs_to_pull))
            );
            result += _concat_diff(branch.diffs_to_pull);

        if(Globals.show_push and len(branch.diffs_to_push) != 0):
            result += tabs() + "{0}:({1})\n".format(
                colors_diffs_to_push("To Push"),
                colors_number(len(branch.diffs_to_push))
            );
            result += _concat_diff(branch.diffs_to_push);
        tab_unindent();

        tab_unindent();
        return result.rstrip(NL);

    ##------------------------------------------------------------------------------
    def print_result(self):
        if(not self.is_dirty()):
            return;

        output_str = "";
        tab_indent();

        ##
        ## Repo name.
        print("{tabs}{repo_name}: ({repo_path})".format(
                tabs=tabs(),
                repo_name=colors_colorize_git_repo_name(self),
                repo_path=self.root_path
        ));

        ##
        ## Branches.
        for branch in self.branches:
            if(not branch.is_dirty()):
                continue;

            ## @notice(stdmatt): Something went very, very, very wrong...
            if(branch is None):
                pdb.set_trace();

            branch_name = colors_branch_name(branch.name);
            status_str  = self._build_status_str(branch);
            diffs_str   = self._build_diffs_str (branch);

            tab_indent();
            output_str = tabs() + branch_name + status_str + diffs_str;
            print(output_str);
            tab_unindent();

        ##
        ## Submodules.
        for submodule in self.submodules:
            submodule.print_result();
        tab_unindent();

        if(not self.is_submodule and not Globals.show_short):
            print();

##------------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="git repository checker",
        usage=get_help_str(),
        add_help=False
    );

    ## Help / Version.
    parser.add_argument("-h", "--help",    dest="show_help",    action="store_true", default=False);
    parser.add_argument("-v", "--version", dest="show_version", action="store_true", default=False);
    parser.add_argument("-Json", "--json", dest="show_json",    action="store_true", default=False);

    ## Remote.
    parser.add_argument("--remote",    dest="update_remote", action="store_true", default=False);
    parser.add_argument("--auto-pull", dest="auto_pull",     action="store_true", default=False);
    parser.add_argument("--force-pull",dest="force_pull",    action="store_true", default=False);

    ## Submodules.
    parser.add_argument("--submodules", dest="submodules", action="store_true", default=False);

    ## Output.
    parser.add_argument("--debug",     dest="is_debug",      action="store_true",  default=False);
    parser.add_argument("--no-colors", dest="color_enabled", action="store_false", default=True );
    parser.add_argument("--show-push", dest="show_push",     action="store_true",  default=False);
    parser.add_argument("--show-pull", dest="show_pull",     action="store_true",  default=False);
    parser.add_argument("--show-all",  dest="show_all",      action="store_true",  default=False);
    parser.add_argument("--short",     dest="show_short",    action="store_true",  default=False);

    parser.add_argument("--all", dest="do_all", action="store_true", default=False);

    ## Start Path.
    parser.add_argument(
        "path",
        default=os.getcwd(),
        nargs="?"
    );

    return parser.parse_args();


##
## Multithread support
##
##------------------------------------------------------------------------------
def update_repo_task(git_repo):
    git_repo.update_remotes();
    git_repo.check_status  ();
    git_repo.try_to_pull   ();

##------------------------------------------------------------------------------
def create_update_task(git_repo):
    x = threading.Thread(target=update_repo_task, args=(git_repo,));
    x.start();
    return x;

##------------------------------------------------------------------------------
def init_repo_task(git_repo):
    git_repo.find_submodules();
    git_repo.find_branches  ();

##------------------------------------------------------------------------------
def create_init_task(git_repo):
    x = threading.Thread(target=init_repo_task, args=(git_repo,));
    x.start();
    return x;


##----------------------------------------------------------------------------##
## Entry Point                                                                ##
##----------------------------------------------------------------------------##
def run():
    if("-Json" in sys.argv[1:] or "--json" in sys.argv[1:]):
        json_args = [arg for arg in sys.argv[1:] if arg in ("-Json", "--json")];
        non_json_args = [arg for arg in sys.argv[1:] if arg not in ("-Json", "--json")];
        if(len(json_args) == 1 and len(non_json_args) == 0):
            print_json_metadata();
        print_json_error(
            "cli.json-metadata-only",
            "--json is currently only supported for root help/version metadata.",
        );

    ##
    ## Parse the command line arguments.
    args = parse_args();

    ## Help / Version.
    if(args.show_help):
        show_help();
    if(args.show_version):
        show_version();
    if(args.show_json):
        print_json_metadata();

    ## Remote.
    Globals.update_remotes = args.update_remote;
    Globals.auto_pull      = args.auto_pull;
    Globals.force_pull     = args.force_pull;

    ## Submodules.
    Globals.submodules = args.submodules;

    ## Output
    if(not args.color_enabled):
        Globals.no_colors = True;

    Globals.is_debug  = args.is_debug;
    Globals.show_pull = args.show_pull;
    Globals.show_push = args.show_push;
    if(args.show_all):
        Globals.show_pull = True;
        Globals.show_push = True;
    if(args.do_all):
        Globals.update_remotes = True;
        Globals.auto_pull      = True;
        Globals.submodules     = True;
        Globals.show_push      = True;
        Globals.show_pull      = True;

    Globals.show_short = args.show_short;

    ## Path.
    Globals.start_path = normalize_path(args.path);

    ##
    ## Load the global .repochecker_ignore.
    if(os.path.isfile(GLOBAL_REPOCHECKER_IGNORE_FULLPATH)):
        log_info("Reading global repochecker_ignore at: ({})", GLOBAL_REPOCHECKER_IGNORE_FULLPATH);
        f = open(GLOBAL_REPOCHECKER_IGNORE_FULLPATH);
        lines = f.readlines();
        f.close();

        for l in lines:
            l = l.strip(" ").replace("\n", "");
            if(os.path.isdir(l)):
                l = normalize_path(l);
                Globals.directories_to_ignore.append(l);
            else:
                log_warn("Invalid path: ({}) - Igoring it...", l);


    ##
    ## Discover the repositories.
    git_repos = [];
    tasks     = [];
    for root, dirs, files in os.walk(Globals.start_path):
        ## @hack(stdmatt): Ignore the recycle bin on Windows.
        ## Probably we wanna check a better way that ensure that it's a bin...
        if("$RECYCLE.BIN" in root):
            log_info("Found a recycle in at: ({})...", root);
            del dirs[0:];
            continue;

        clean_root = normalize_path(root);
        if(clean_root in Globals.directories_to_ignore):
            log_info("Global .repochecker_ignore says to ignore path: ({})...", root);
            continue;
        if(".repochecker_ignore" in files and os.path.abspath(root) != GLOBAL_REPOCHECKER_IGNORE_DIRPATH):
            log_info("Found .repochecker_ignore in ({})...", root);
            del dirs[0:];
            continue;
        if(not has_git_repo_marker(dirs, files)):
            continue;

        git_repo = GitRepo(root);
        git_repos.append(git_repo);

        x = create_init_task(git_repo);
        if(x is not None):
            tasks.append(x);

        log_debug("");
        del dirs[0:];

    for t in tasks:
        t.join();

    ##
    ## Update the Repositories.
    tasks = [];
    log_info("Found {0} repos...", len(git_repos));
    for i in range(0, len(git_repos)):
        git_repo = git_repos[i];
        log_info("Updating Repository ({}) - ({} of {})", git_repo.name, i+1, len(git_repos));

        x = create_update_task(git_repo);
        if(x is not None):
            tasks.append(x);

    for t in tasks:
        t.join();

    ##
    ## Present Repositories.
    for i in range(0, len(git_repos)):
        git_repo = git_repos[i];
        git_repo.print_result();

if __name__ == "__main__":
    run();