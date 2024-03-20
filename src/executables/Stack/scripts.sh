echo "[INFO] Stack build script executing on directory:$1"
cd $1
stack ls dependencies json > stack_deps.json