#!/usr/bin/env bash
##~---------------------------------------------------------------------------##
##                        _      _                 _   _                      ##
##                    ___| |_ __| |_ __ ___   __ _| |_| |_                    ##
##                   / __| __/ _` | '_ ` _ \ / _` | __| __|                   ##
##                   \__ \ || (_| | | | | | | (_| | |_| |_                    ##
##                   |___/\__\__,_|_| |_| |_|\__,_|\__|\__|                   ##
##                                                                            ##
##  File      : install.sh                                                    ##
##  Project   : repochecker                                                   ##
##  Date      : Jan 09, 2020                                                  ##
##  License   : GPLv3                                                         ##
##  Author    : stdmatt <stdmatt@pixelwizards.io>                             ##
##  Copyright : stdmatt - 2020                                                ##
##                                                                            ##
##  Description :                                                             ##
##                                                                            ##
##---------------------------------------------------------------------------~##

##
## Imports
source "/usr/local/src/stdmatt/shellscript_utils/main.sh";

##
## Variables
SCRIPT_DIR=$(pw_get_script_dir);

##
## Script
pw_as_super_user pip3 uninstall repochecker --yes
pw_as_super_user python3 "$SCRIPT_DIR/setup.py" install
