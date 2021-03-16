#!/usr/bin/env bash
## @todo(stdmatt): Check if this script is still relevant - 3/16/2021, 10:49:59 AM

##----------------------------------------------------------------------------##
## Imports                                                                    ##
##----------------------------------------------------------------------------##
source /usr/local/src/stdmatt/shellscript_utils/main.sh


##----------------------------------------------------------------------------##
## Variables                                                                  ##
##----------------------------------------------------------------------------##
SCRIPT_DIR="$(pw_get_script_dir)";
PROJECT_ROOT="$(pw_abspath "${SCRIPT_DIR}/..")";

SRC_FILE="${PROJECT_ROOT}/repochecker/repochecker.py";
SETUP_FILE="${PROJECT_ROOT}/setup.py";


##----------------------------------------------------------------------------##
## Script                                                                     ##
##----------------------------------------------------------------------------##
BUMP_THE_VERSION="$(pw_get_program_path "bump-the-version")";
if [ -z "$BUMP_THE_VERSION" ]; then
    pw_log_fatal "Coundn't find (bump-the-version) program - Aborting...";
fi;

"${BUMP_THE_VERSION}" "${SRC_FILE}"   "__version__ " bump "$1";
"${BUMP_THE_VERSION}" "${SETUP_FILE}" "version="     bump "$1";
