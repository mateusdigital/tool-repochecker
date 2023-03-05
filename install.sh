#!/usr/bin/env bash
##----------------------------------------------------------------------------##
##                        _      _                 _   _                      ##
##                       | |    | |               | | | |                     ##
##                    ___| |_ __| |_ __ ___   __ _| |_| |_                    ##
##                   / __| __/ _` | '_ ` _ \ / _` | __| __|                   ##
##                   \__ \ || (_| | | | | | | (_| | |_| |_                    ##
##                   |___/\__\__,_|_| |_| |_|\__,_|\__|\__|                   ##
##                                                                            ##
##                                                                            ##
##  File      : install.sh                                                    ##
##  Project   : repochecker                                                   ##
##  Date      : 16 Mar, 2021                                                  ##
##  License   : GPLv3                                                         ##
##  Author    : stdmatt <stdmatt@pixelwizards.io>                             ##
##  Copyright : stdmatt - 2021, 2022, 2023                                    ##
##                                                                            ##
##  Description :                                                             ##
##                                                                            ##
##---------------------------------------------------------------------------~##

##----------------------------------------------------------------------------##
## Constants                                                                  ##
##----------------------------------------------------------------------------##
##------------------------------------------------------------------------------
## Script
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)";

## Program
PROGRAM_NAME="repochecker";

PROGRAM_INSTALL_DIR="${HOME}/.mateus-earth/bin";

SRC_PATH="${SCRIPT_DIR}/${PROGRAM_NAME}/main.py"
INSTALL_PATH="${PROGRAM_INSTALL_DIR}/${PROGRAM_NAME}"

##----------------------------------------------------------------------------##
## Script                                                                     ##
##----------------------------------------------------------------------------##
##------------------------------------------------------------------------------
echo "---> Installing ...";

## Create the install directory...
if [ ! -d "${PROGRAM_INSTALL_DIR}" ]; then
    echo "---> Creating directory at: ";
    echo "     ${PROGRAM_INSTALL_DIR}";
fi;

## Copy the file to the install dir...
cp -f "$SRC_PATH" "$INSTALL_PATH";

echo "---> $PROGRAM_NAME was installed at: ($PROGRAM_INSTALL_DIR)";
echo "     You might need add it to the PATH";

echo "---> Done... ;D";
echo "";
