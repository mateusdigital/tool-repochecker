
##
## Constants
##
##------------------------------------------------------------------------------
## Script
$SCRIPT_FULLPATH = $MyInvocation.MyCommand.Path;
$SCRIPT_DIR      = Split-Path "$SCRIPT_FULLPATH" -Parent;
$HOME_DIR        = "$env:USERPROFILE";
## Program
$PROGRAM_NAME         = "repochecker";
$PROGRAM_INSTALL_PATH = "$HOME_DIR/.stcmatt_bin/$PROGRAM_NAME";

##
## Script
##
##------------------------------------------------------------------------------
echo "Installing ...";

## Create the install directory...
if (-not (Test-Path -LiteralPath $PROGRAM_INSTALL_PATH)) {
    echo "Creating directory at: ";
    echo "    $PROGRAM_INSTALL_PATH";
    New-Item -Path $PROGRAM_INSTALL_PATH -ItemType Directory;
}

## Copy the file to the install dir...
cp $SCRIPT_DIR/$PROGRAM_NAME/main.py    $PROGRAM_INSTALL_PATH/main.py
echo "@echo off `npython3 $PROGRAM_INSTALL_PATH/main.py" | Out-File -Encoding ASCII -FilePath $PROGRAM_INSTALL_PATH/repochecker.bat


## @TODO(stdmatt): Implement a way to add the directory to the path so we can use
## the repochecker from anyware... 3/16/2021, 12:43:07 PM


# ##
# ## Add the things to PATH
# ## thanks to: https://codingbee.net/powershell/powershell-make-a-permanent-change-to-the-path-environment-variable
# $old_path = (Get-ItemProperty -Path 'Registry::HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Session Manager\Environment' -Name PATH).path;
# if( $old_path.IndexOf("REPOCHECKER_DIR") -eq -1 ) {
#     echo "Setting path...";

#     $PATH_DIR = "$PROGRAM_INSTALL_PATH";
#     $new_path = "$old_path;$PATH_DIR";

#     echo "   New path: $new_path";

#     [System.Environment]::SetEnvironmentVariable("REPOCHECKER_DIR", $PATH_DIR, [System.EnvironmentVariableTarget]::User);
#     Set-ItemProperty -Path 'Registry::HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Session Manager\Environment' -Name PATH -Value $new_path;

#     echo "";
# }

# echo "Done... ;D";
# echo "";
# Write-Host -NoNewline -Object "Press any key continue...";
# ##$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown");
