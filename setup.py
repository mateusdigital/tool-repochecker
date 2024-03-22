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
##  File      : setup.py                                                      ##
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
from setuptools import setup, find_packages

## -----------------------------------------------------------------------------
setup(
    name="repochecker",
    version="3.1.0",
    description="Checks and displays informations about git repos.",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "repochecker = repochecker.main:run",
        ],
    },
)
