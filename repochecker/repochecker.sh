#!/usr/bin/env bash
function repochecker() {
    local script_fullpath="${BASH_SOURCE[0]}"
    local script_dir
    script_dir="$(dirname "$script_fullpath")"
    local repochecker_exe="${script_dir}/repochecker.py"
    local -a python_cmd=()

    if command -v "python3" >/dev/null 2>&1 && python3 --version >/dev/null 2>&1; then
        python_cmd=("python3")
    elif command -v "python" >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
        python_cmd=("python")
    elif command -v "py" >/dev/null 2>&1 && py -3 --version >/dev/null 2>&1; then
        python_cmd=("py" "-3")
    else
        echo "[repochecker] Missing a working Python interpreter (tried: python3, python, py -3)"
        return 1
    fi

    if [ ! -f "$repochecker_exe" ]; then
        echo "[repochecker] Missing ($repochecker_exe)"
        return 1
    fi

    "${python_cmd[@]}" "$repochecker_exe" "$@"
}
