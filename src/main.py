#!/usr/bin/env python3
import os;
import os.path;
import glob;
from pathlib import Path;

def get_home_path():
    return os.path.abspath(os.path.expanduser("~"));

def main():
    start_path = os.path.join(
        get_home_path(),
        "Documents/Projects/stdmatt/"
    );

    for a in Path(start_path).rglob(".git"):
        print(a);

main();