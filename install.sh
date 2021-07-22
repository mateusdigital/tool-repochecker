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
##  Copyright : stdmatt - 2020, 2021                                          ##
##                                                                            ##
##  Description :                                                             ##
##                                                                            ##
##---------------------------------------------------------------------------~##

##
## Imports
##
source "$HOME/.ark/ark_shlib/main.sh"

##
## Constants
##
##------------------------------------------------------------------------------
## Script
SCRIPT_DIR=$(ark_get_script_dir);
## Program
PROGRAM_NAME="repochecker";
PROGRAM_SOURCE_PATH="$SCRIPT_DIR/$PROGRAM_NAME";
PROGRAM_INSTALL_PATH="$HOME/.stdmatt_bin";
PROGRAM_INSTALL_SUBPATH="$PROGRAM_INSTALL_PATH/$PROGRAM_NAME";

##
## Script
##
##------------------------------------------------------------------------------
echo "Installing ...";

## Create the install directory...
if [ ! -d "$PROGRAM_INSTALL_SUBPATH" ]; then
    echo "Creating directory at: ";
    echo "    $PROGRAM_INSTALL_SUBPATH";
    mkdir -p "$PROGRAM_INSTALL_SUBPATH" > /dev/null;
fi;

## Copy the file to the install dir...
cp -f "$PROGRAM_SOURCE_PATH/main.py" "$PROGRAM_INSTALL_SUBPATH/$PROGRAM_NAME";
chmod 744 "$PROGRAM_INSTALL_SUBPATH/$PROGRAM_NAME";

echo "$PROGRAM_NAME was installed at:";
echo "    $PROGRAM_INSTALL_SUBPATH";
echo "You might need add it to the PATH";
echo '    PATH=$PATH:'"$PROGRAM_INSTALL_SUBPATH"

echo "Done... ;D";
echo "";
