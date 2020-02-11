#!/usr/bin/env bash

##
## Imports
source "/usr/local/src/stdmatt/shellscript_utils/main.sh";

##
## Variables
SCRIPT_DIR=$(pw_get_script_dir);

##
## Script
pw_as_super_user pip3 uninstall repochecker
pw_as_super_user python3 "$SCRIPT_DIR/setup.py" install
