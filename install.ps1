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
##  File      : install.ps1                                                   ##
##  Project   : repochecker                                                   ##
##  Date      : 2024-03-22                                                    ##
##  License   : See project's COPYING.TXT for full info.                      ##
##  Author    : mateus.digital <hello@mateus.digital>                         ##
##  Copyright : mateus.digital - 2024                                         ##
##                                                                            ##
##  Description :                                                             ##
##                                                                            ##
##---------------------------------------------------------------------------~##

## -----------------------------------------------------------------------------
Write-Output "==> Installing repochecker...";

## -----------------------------------------------------------------------------
$PROGRAM_NAME = "repochecker"
$INSTALL_ROOT = "${HOME}/.mateusdigital/bin";
$INSTALL_DIR  = "${INSTALL_ROOT}/${PROGRAM_NAME}";

## -----------------------------------------------------------------------------
New-Item -Path "${INSTALL_DIR}" -ItemType Directory -Force | Out-Null;
Copy-Item ./repochecker/main.py "${INSTALL_DIR}/_repochecker.py"
Write-Output "python3 ${INSTALL_DIR}/_repochecker.py `$args" | Out-File "${INSTALL_ROOT}/repochecker.ps1";

Write-Output "$PROGRAM_NAME was installed at:";
Write-Output "    $INSTALL_ROOT";
Write-Output "You might need add it to the PATH";

Write-Output "Done... ;D";
Write-Output "";
