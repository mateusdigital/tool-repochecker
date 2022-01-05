##----------------------------------------------------------------------------##
##                        _      _                 _   _                      ##
##                       | |    | |               | | | |                     ##
##                    ___| |_ __| |_ __ ___   __ _| |_| |_                    ##
##                   / __| __/ _` | '_ ` _ \ / _` | __| __|                   ##
##                   \__ \ || (_| | | | | | | (_| | |_| |_                    ##
##                   |___/\__\__,_|_| |_| |_|\__,_|\__|\__|                   ##
##                                                                            ##
##                                                                            ##
##  File      : install.ps1                                                   ##
##  Project   : repochecker                                                   ##
##  Date      : 16 Mar, 2021                                                  ##
##  License   : GPLv3                                                         ##
##  Author    : stdmatt <stdmatt@pixelwizards.io>                             ##
##  Copyright : stdmatt - 2021, 2022                                          ##
##                                                                            ##
##  Description :                                                             ##
##                                                                            ##
##---------------------------------------------------------------------------~##

##----------------------------------------------------------------------------##
## Constants                                                                  ##
##----------------------------------------------------------------------------##
##------------------------------------------------------------------------------
## Script
$SCRIPT_FULLPATH = $MyInvocation.MyCommand.Path;
$SCRIPT_DIR      = Split-Path "$SCRIPT_FULLPATH" -Parent;
$HOME_DIR        = "$env:USERPROFILE";
## Program
$PROGRAM_NAME         = "repochecker";
$PROGRAM_SOURCE_PATH  = "$SCRIPT_DIR/$PROGRAM_NAME";
$PROGRAM_INSTALL_PATH = "$HOME_DIR/.stdmatt_bin";
$PROGRAM_INSTALL_SUBPATH = "$PROGRAM_INSTALL_PATH/$PROGRAM_NAME";


##----------------------------------------------------------------------------##
## Script                                                                     ##
##----------------------------------------------------------------------------##
##------------------------------------------------------------------------------
echo "Installing ...";

## Create the install directory...
if (-not (Test-Path -LiteralPath $PROGRAM_INSTALL_SUBPATH)) {
    echo "Creating directory at: ";
    echo "    $PROGRAM_INSTALL_SUBPATH";
    $null = New-Item -Path $PROGRAM_INSTALL_SUBPATH -ItemType Directory;
}

## Copy the file to the install dir...
cp -Force $PROGRAM_SOURCE_PATH/main.py     `
          $PROGRAM_INSTALL_SUBPATH/main.py

echo "@echo off `npython3 $PROGRAM_INSTALL_SUBPATH/main.py %1 %2 %3 %4 %5 %6 %7 %8 %9" `
    | Out-File -Encoding ASCII -FilePath $PROGRAM_INSTALL_PATH/$PROGRAM_NAME.bat

echo "$PROGRAM_NAME was installed at:";
echo "    $PROGRAM_INSTALL_PATH";
echo "You might need add it to the PATH";

echo "Done... ;D";
echo "";
