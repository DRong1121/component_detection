echo "[INFO] Rebar build script executing on directory:$1"
cd $1
rebar3 tree -v > rebar_tree.txt