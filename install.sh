#!/usr/bin/env bash

##
## Imports
source "/usr/local/src/stdmatt/shellscript_utils/main.sh";

##
## Variables
_SCRIPT_DIR="$(pw_get_script_dir)";
_IS_DEV_MODE="true";
INSTALL_BIN_DIR="/usr/local/bin";
SRC_DIR="$_SCRIPT_DIR/src";

##
## Install.
COPY_OR_LINK="cp -fv"; 
test "$_IS_DEV_MODE" == "true" && COPY_OR_LINK="ln -fv";

$COPY_OR_LINK "$SRC_DIR/main.py" "$INSTALL_BIN_DIR/repochecker";
chmod 755 "$INSTALL_BIN_DIR/repochecker";

