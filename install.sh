#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
home_dir="${HOME:-$USERPROFILE}"

if command -v cygpath >/dev/null 2>&1 && [[ "$home_dir" =~ ^[A-Za-z]:[\\/] ]]; then
    home_dir="$(cygpath -u "$home_dir")"
fi

program_name="repochecker"
root_path="${home_dir}/.saturnosoftware/${program_name}"
bin_path="${root_path}/bin"
config_path="${root_path}/config"
data_path="${root_path}/data"

if [ -d "${script_dir}/App" ]; then
    source_path="${script_dir}/App"
elif [ -d "${script_dir}/repochecker" ]; then
    source_path="${script_dir}/repochecker"
else
    echo "[repochecker] Missing packaged App/ or source repochecker/ directory."
    exit 1
fi

package_json="${script_dir}/package.json"
if [ ! -f "$package_json" ]; then
    echo "[repochecker] Missing package.json metadata file."
    exit 1
fi

echo "Installing ..."

for dir in "$root_path" "$bin_path" "$config_path" "$data_path"; do
    if [ ! -d "$dir" ]; then
        echo "  Creating: $dir"
        mkdir -p "$dir"
    fi
done

if [ -f "${source_path}/repochecker.py" ]; then
    cp -f "${source_path}/repochecker.py" "${bin_path}/repochecker.py"
elif [ -f "${source_path}/main.py" ]; then
    cp -f "${source_path}/main.py" "${bin_path}/repochecker.py"
else
    echo "[repochecker] Missing install payload: repochecker.py or main.py"
    exit 1
fi
cp -f "${source_path}/repochecker.ps1" "${bin_path}/repochecker.ps1"
cp -f "${source_path}/repochecker.sh" "${bin_path}/repochecker.sh"
cp -f "$package_json" "${root_path}/package.json"

if [ ! -f "${bin_path}/repochecker.py" ] || [ ! -f "${bin_path}/repochecker.sh" ]; then
    echo "[repochecker] Installed payload is incomplete."
    exit 1
fi

if command -v "python3" >/dev/null 2>&1; then
    python3 "${bin_path}/repochecker.py" --version >/dev/null
elif command -v "python" >/dev/null 2>&1; then
    python "${bin_path}/repochecker.py" --version >/dev/null
else
    echo "[repochecker] Missing a working Python interpreter for the post-install smoke test."
    exit 1
fi

echo ""
echo "$program_name was installed at:"
echo "  $root_path"
echo "Binary directory:"
echo "  $bin_path"
echo "Data directory:"
echo "  $data_path"
echo ""
echo "You might need to add it to the PATH."
echo "  Or source it directly: source \"$bin_path/repochecker.sh\""
echo ""
echo "Done... ;D"
