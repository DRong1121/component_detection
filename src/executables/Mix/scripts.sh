echo "[INFO] Mix build script executing on directory:$1"
cd $1
mix deps.compile
mix deps.get