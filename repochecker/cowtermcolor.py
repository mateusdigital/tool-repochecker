##~---------------------------------------------------------------------------##
##                        _      _                 _   _                      ##
##                    ___| |_ __| |_ __ ___   __ _| |_| |_                    ##
##                   / __| __/ _` | '_ ` _ \ / _` | __| __|                   ##
##                   \__ \ || (_| | | | | | | (_| | |_| |_                    ##
##                   |___/\__\__,_|_| |_| |_|\__,_|\__|\__|                   ##
##                                                                            ##
##  File      : cowtermcolor.py                                               ##
##  Project   : repochecker                                                   ##
##  Date      : Feb 06, 2020                                                  ##
##  License   : GPLv3                                                         ##
##  Author    : stdmatt <stdmatt@pixelwizards.io>                             ##
##  Copyright : stdmatt - 2020                                                ##
##                                                                            ##
##  Description :                                                             ##
##                                                                            ##
##---------------------------------------------------------------------------~##
#coding=utf8

"""
Smart color formating for output in terminal.

cowtermcolor is a library to ease the terminal coloring.

It was inspired by the Amazing Cow's C++ Termcolor_cpp
(http://www.github.com/AmazingCow-Libs/Termcolor_cpp), which was
inspired by the python's termcolor

With cowtermcolor_py we can:
   * Use the colored function - "Same" as the Termcolor_cpp
                                 colored function.
   * Use standalone functions - Like print red("MyString")) + reset();
   * Use functor objects      - This is nice because we can setup
                                the coloring options and use it later,
                                possible multiple times.

Smart coloring:
    What is really nice in cowtermcolor_py and in Termcolor_cpp is both
    libs knows if the output is the terminal or not,  i.e. them knows
    if the stdout is attached to a tty.


And what we gain with this?
    1. By default it will output the coloring escape sequences
       only if the stdout is a tty.
    2. Cleaner code - We don't need check the output anymore
       (If we want the default).
    3. More cleaner code - To enable, or disable the coloring
       we can set it only once.
"""

## Imports ##
import os
import sys;
import re;

__version__   = "0.2.2";
__author__    = "n2omatt - <n2omatt@amazingcow.com>";
__date__      = "May 4, 2016";
__copyright__ = "Copyright 2016 - Amazing Cow "
__license__   = 'GPLv3'



################################################################################
## Color Mode / Convert Mode Classes                                          ##
################################################################################
class ColorMode(object):
    """
Global Color Modes - MODIFY ALL COLORING FUNCTIONS.

This class defines how the coloring functions will behave.

To change the behavior assign a new value to ColorMode.mode.

The possible Color modes are:
    ONLY_IF_TERMINAL
        Color escapes codes are only put into the strings if
        the os.stdout is assigned to a tty.

        This enables code to don't care the type of the stdout
        i.e. if a pipe, file, or tty.

        If the os.stdout isn't assigned to a tty all coloring
        functions will return the unmodified string.

    ALWAYS
        Don't care for where the os.stdout is assigned.
        Put the coloring escape sequences anyway.

    NEVER
        Don't care for where the os.stdout is assigned.
        DO NOT put the coloring escape sequences anyway.

    DEFAULT
        Same of ONLY_IF_TERMINAL
"""
    ONLY_IF_TERMINAL = 0;
    ALWAYS           = 1;
    NEVER            = 2;
    DEFAULT          = ONLY_IF_TERMINAL;

    mode = DEFAULT;


class ConvertMode(object):
    """
Global Convert Modes - MODIFY ALL COLORING FUNCTIONS.

This class defines how the conversions will be applied when values
of types is passed to any coloring function.

To change the behavior assign a new value to ConvertMode.mode.

The possible convert modes are:
    ALL_TYPES_TO_STR
        Any given type, but str, will be passed into str().

    ALL_TYPES_TO_TO_EMPTY_STR
        Any given type, but str, will be replaced by an empty str.

    NONE_TYPE_TO_EMPTY_STR
        Only the None type will be replaced by an empty str
        all other types will passed into str().

    RAISE_VALUE_ERROR_FOR_ALL_TYPES
        A ValueError exception will be raised if the type isn't str.

    RAISE_VALUE_ERROR_FOR_NONE_TYPE
        A ValueError exception will be raised only for None type.

    DEFAULT
        Equal to ALL_TYPES_TO_STR;
"""
    ALL_TYPES_TO_STR                = 0;
    ALL_TYPES_TO_TO_EMPTY_STR       = 1;
    NONE_TYPE_TO_EMPTY_STR          = 2;
    RAISE_VALUE_ERROR_FOR_ALL_TYPES = 3;
    RAISE_VALUE_ERROR_FOR_NONE_TYPE = 4;
    DEFAULT                         = ALL_TYPES_TO_STR;

    mode = DEFAULT;


################################################################################
## Color Mode                                                                 ##
################################################################################
class Color(object):
    """
Holds a set of coloring parameters into a nice object.

This enables you group a set of different parameters
and reuse them with ease.

Example:
    greyOnRedBlinking      = Color(GREY, RED, [BLINK]);
    redOnBlueBoldUnderline = Color(GREY, RED, [BOLD, UNDERLINE]);

    print greyOnRedBlinking("Hi there...");
    print redOnBlueBoldUnderline("I <3 cowtermcolor");
"""

    def __init__(self, fg = None, bg = None, list_of_attr = None):
        """
        No validation checks are made on given argument values
        Users should call it only with the 'constants'
        defined in this module.
        """
        self._foreground = fg;
        self._background = bg;
        self._attrs      = list_of_attr;


    def __call__(self, s = "", auto_reset=True):
        """__call__(self, s = "") -> str

Makes the object callable - It will apply
the foreground colors, next the background colors
and after that the attributes.

Notice that this function is affected by:
ColorMode.mode and ConvertMode.mode.

Example:
    redBlinking = Color(RED, None, BLINK);
    print redBlinking("Roses are red");
"""
        r = "";
        if(self._foreground is not None):
            r = _put_color(self._foreground);

        if(self._background is not None):
            r += _put_color(self._background);

        if(self._attrs is not None):
            for attr in self._attrs:
                r += _put_color(attr);

        r += _convert_value(s);

        if(auto_reset):
             r+= _put_color(RESET);

        return r;




################################################################################
## Color Constants                                                            ##
################################################################################
## Reset ##
RESET = 0;
## Foreground Colors ##
BLACK   = 30;
GREY    = 30;
RED     = 31;
GREEN   = 32;
YELLOW  = 33;
BLUE    = 34;
MAGENTA = 35;
CYAN    = 36;
WHITE   = 37;
BRIGHT_BLACK   = 90;
BRIGHT_GREY    = 90;
BRIGHT_RED     = 91;
BRIGHT_GREEN   = 92;
BRIGHT_YELLOW  = 93;
BRIGHT_BLUE    = 94;
BRIGHT_MAGENTA = 95;
BRIGHT_CYAN    = 96;
BRIGHT_WHITE   = 97;
## Background Colors ##
ON_BLACK   = 40;
ON_RED     = 41;
ON_GREEN   = 42;
ON_YELLOW  = 43;
ON_BLUE    = 44;
ON_MAGENTA = 45;
ON_CYAN    = 46;
ON_WHITE   = 47;
ON_BRIGHT_BLACK   = 100;
ON_BRIGHT_RED     = 101;
ON_BRIGHT_GREEN   = 102;
ON_BRIGHT_YELLOW  = 103;
ON_BRIGHT_BLUE    = 104;
ON_BRIGHT_MAGENTA = 105;
ON_BRIGHT_CYAN    = 106;
ON_BRIGHT_WHITE   = 107;
## Attributes ##
BLINK     = 5;
BOLD      = 1;
CONCEALED = 8;
DARK      = 2;
REVERSE   = 7;
UNDERLINE = 4;



################################################################################
## Colored Function                                                           ##
################################################################################
def colored(s, fg = None, bg = None, attrs = None):
    """colored(s, fg=None, bg=None, attrs=None) -> str

    Builds the colored output in one function.
    It will put the foreground color, then the background and after all
    the attributes if there are any.

    str        - The string that will be colored.(Mandatory)
    foreground - A valid foreground color code.  (Optional)
    background - A valid background color code.  (Optional)
    attributes - A valid attributes codes.       (Optional)

    This function is affected by the values of:
    ColorMode.mode and ConvertMode.mode.

    This function will not check the validity of the color codes,
    so is user's responsibility to ensure that them are valid.

    The best bet is use the cowtermcolor constants.
"""
    r = "";
    #Foreground.
    if(fg is not None):
        r = _put_color(fg);

    #Background.
    if(bg is not None):
        r += _put_color(bg);

    #Attributes.
    if(attrs is not None):
        for attr in attrs:
            r += _put_color(attr);

    r += _convert_value(s) + _put_color(RESET);
    return r;


################################################################################
## RESET                                                                      ##
################################################################################
def reset(s = ""):
    """reset(s) -> str
Put the reset escape sequence in front of the 's'
canceling all previous coloring.

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(RESET) + _convert_value(s);


################################################################################
## FOREGROUND FUNCTION                                                        ##
################################################################################
def grey(s = ""):
    """grey(s) -> str
Put the grey foreground escape sequence in front of the 's'.

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(GREY) + _convert_value(s);


def red(s = ""):
    """red(s) -> str
Put the red escape foreground sequence in front of the 's'.

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(RED) + _convert_value(s);


def green(s = ""):
    """green(s) -> str
Put the green foreground escape sequence in front of the 's'.

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(GREEN) + _convert_value(s);


def yellow(s = ""):
    """yellow(s) -> str
Put the yellow foreground escape sequence in front of the 's'.

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(YELLOW) + _convert_value(s);


def blue(s = ""):
    """blue(s) -> str
Put the blue foreground escape sequence in front of the 's'.

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(BLUE) + _convert_value(s);


def magenta(s = ""):
    """magenta(s) -> str
Put the grey foreground magenta sequence in front of the 's'.

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(MAGENTA) + _convert_value(s);


def cyan(s = ""):
    """cyan(s) -> str
Put the cyan foreground escape sequence in front of the 's'.

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(CYAN) + _convert_value(s);


def white(s = ""):
    """white(s) -> str
Put the white foreground escape sequence in front of the 's'.

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(WHITE) + _convert_value(s);


################################################################################
## BACKGROUND FUNCTIONS                                                       ##
################################################################################
def on_grey(s = ""):
    """on_grey(s) -> str
Put the grey background escape sequence in front of 's'

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(ON_GREY) + _convert_value(s);


def on_red(s = ""):
    """on_red(s) -> str
Put the red background escape sequence in front of 's'

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(ON_RED) + _convert_value(s);


def on_green(s = ""):
    """on_green(s) -> str
Put the green background escape sequence in front of 's'

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(ON_GREEN) + _convert_value(s);


def on_yellow(s = ""):
    """on_yellow(s) -> str
Put the yellow background escape sequence in front of 's'

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(ON_YELLOW) + _convert_value(s);


def on_blue(s = ""):
    """on_blue(s) -> str
Put the blue background escape sequence in front of 's'

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(ON_BLUE) + _convert_value(s);


def on_magenta(s = ""):
    """on_magenta(s) -> str
Put the magenta background escape sequence in front of 's'

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(ON_MAGENTA) + _convert_value(s);


def on_cyan(s = ""):
    """on_cyan(s) -> str
Put the cyan background escape sequence in front of 's'

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(ON_CYAN) + _convert_value(s);


def on_white(s = ""):
    """on_white(s) -> str
Put the white background escape sequence in front of 's'

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(ON_WHITE) + _convert_value(s);


################################################################################
## ATTRIBUTES FUNCTIONS                                                       ##
################################################################################
def bold(s = ""):
    """bold(s) -> str
Put the bold attribute escape sequence in front of 's'.

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(BOLD) + _convert_value(s);


def dark(s = ""):
    """dark(s) -> str
Put the dark attribute escape sequence in front of 's'.

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(DARK) + _convert_value(s);


def underline(s = ""):
    """underline(s) -> str
Put the underline attribute escape sequence in front of 's'.

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(UNDERLINE) + _convert_value(s);


def blink(s = ""):
    """blink(s) -> str
Put the blink attribute escape sequence in front of 's'.

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(BLINK) + _convert_value(s);


def reverse(s = ""):
    """reverse(s) -> str
Put the reverse attribute escape sequence in front of 's'.

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(REVERSE) + _convert_value(s);


def conceale(s = ""):
    """conceale(s) -> str
Put the conceale attribute escape sequence in front of 's'.

This function is affected by the values of:
ColorMode.mode and ConvertMode.mode.
"""
    return _put_color(CONCEALE) + _convert_value(s);



################################################################################
## HELPER FUNCTIONS                                                           ##
################################################################################
def code_to_escape_str(code):
    """code_to_escape_str(code) -> str
Returns the raw escape sequence string.

No validation is made to ensure that the resulting
sequence will be valid - Users should call it only
with the 'constants' defined in this module.

Example:
    code_to_escape_str(cowtercolor.BLUE) -> "\\033[34m"
"""
    return "%s%d%s" %(__START_ESCAPE_STR, code, __END_ESCAPE_STR);


def remove_all_escape_codes(s):
    """remove_all_escape_codes(s) -> str
Removes (if any) all escapes sequences in the 's' string.

Example:
    remove_all_escape_codes(green("Amazing Cow")) -> "Amazing Cow"
    remove_all_escape_codes("Plain string") -> "Plain string"
"""
    return re.sub("\033\[\d+m", "", s);


def str_len(s):
    """str_len(s) -> integer

Count the number of chars in string disregarding all coloring
escape sequences - Same as len(remove_all_escape_codes(s))
"""
    return len(remove_all_escape_codes(s));



################################################################################
## Private Stuff                                                              ##
################################################################################
__START_ESCAPE_STR = "\033[";
__END_ESCAPE_STR   = "m";

def _convert_value(value):
    if(type(value) == str):
        return value;

    if(ConvertMode.mode == ConvertMode.ALL_TYPES_TO_STR):
        return str(value);

    if(ConvertMode.mode == ConvertMode.ALL_TYPES_TO_TO_EMPTY_STR):
        return "";

    if(ConvertMode.mode == ConvertMode.NONE_TYPE_TO_EMPTY_STR):
        if(value is None): return "";
        else:              return str(value);

    if(ConvertMode.mode == ConvertMode.RAISE_VALUE_ERROR_FOR_ALL_TYPES):
        raise ValueError("COWTODO: Add a description....");

    if(ConvertMode.mode == ConvertMode.RAISE_VALUE_ERROR_FOR_NONE_TYPE):
        if(value is None): raise ValueError("COWTODO: Add a description....");
        else:              return str(value);


def _put_color(color):
    if(ColorMode.mode == ColorMode.ALWAYS):
        return code_to_escape_str(color);
    elif(ColorMode.mode == ColorMode.NEVER):
        return "";
    #ColorMode.mode == ONLY_IN_TERMINAL
    elif(os.isatty(sys.stdout.fileno())):
        return code_to_escape_str(color);

    return ""


if __name__ == '__main__':
    red("ola");
    pass;


