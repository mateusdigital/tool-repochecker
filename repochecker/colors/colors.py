##~---------------------------------------------------------------------------##
##                        _      _                 _   _                      ##
##                    ___| |_ __| |_ __ ___   __ _| |_| |_                    ##
##                   / __| __/ _` | '_ ` _ \ / _` | __| __|                   ##
##                   \__ \ || (_| | | | | | | (_| | |_| |_                    ##
##                   |___/\__\__,_|_| |_| |_|\__,_|\__|\__|                   ##
##                                                                            ##
##  File      : colors.py                                                     ##
##  Project   : repochecker                                                   ##
##  Date      : Apr 09, 2020                                                  ##
##  License   : GPLv3                                                         ##
##  Author    : stdmatt <stdmatt@pixelwizards.io>                             ##
##  Copyright : stdmatt - 2020                                                ##
##                                                                            ##
##  Description :                                                             ##
##                                                                            ##
##---------------------------------------------------------------------------~##

import os;
from mcow_py_termcolor import termcolor;

##------------------------------------------------------------------------------
termcolor.color_mode = termcolor.COLOR_MODE_ALWAYS;


##------------------------------------------------------------------------------
def disable_coloring():
    termcolor.color_mode = termcolor.COLOR_MODE_NEVER;


##------------------------------------------------------------------------------
def green  (s): return termcolor.colored(s, termcolor.GREEN  );
def red    (s): return termcolor.colored(s, termcolor.RED    );
def blue   (s): return termcolor.colored(s, termcolor.BLUE   );
def yellow (s): return termcolor.colored(s, termcolor.YELLOW );
def white  (s): return termcolor.colored(s, termcolor.WHITE  );
def magenta(s): return termcolor.colored(s, termcolor.MAGENTA);
def cyan   (s): return termcolor.colored(s, termcolor.CYAN   );

##------------------------------------------------------------------------------
def number(n): return cyan   (p);
def path  (p): return magenta(p);


##------------------------------------------------------------------------------
def repo_name (name): return magenta(name);
def repo_clean(name): return green  (name);
def repo_dirty(name): return red    (name);

def colorize_git_repo_name(git_repo):
    pretty_name = os.path.basename(git_repo.root_path);
    if(git_repo.is_dirty()):
        pretty_name = repo_dirty(pretty_name);
    else:
        pretty_name = repo_clean(pretty_name);

    prefix = "[Submodule]" if git_repo.is_submodule else "[Repo]";
    path   = git_repo.root_path;

    return "{0} {1} ".format(prefix, pretty_name, path);


##------------------------------------------------------------------------------
def branch_name(s): return termcolor.colored(s, termcolor.GREY);

def branch_modified (s): return yellow(s);
def branch_added    (s): return green (s);
def branch_deleted  (s): return red   (s);
def branch_renamed  (s): return yellow(s);
def branch_copied   (s): return yellow(s);
def branch_updated  (s): return yellow(s);
def branch_untracked(s): return termcolor.colored(s, fg=None, bg=termcolor.ON_RED);


##------------------------------------------------------------------------------
def diffs_to_pull(s): return yellow(s);
def diffs_to_push(s): return green (s);


##------------------------------------------------------------------------------
def pulling_repo_name  (s): return termcolor.colored(s, termcolor.MAGENTA);
def pulling_branch_name(s): return termcolor.colored(s, termcolor.CYAN);


##------------------------------------------------------------------------------
def commit_sha(s): return red  (s);
def commit_msg(s): return white(s);


