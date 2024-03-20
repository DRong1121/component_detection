echo "[INFO] Sbt build script executing on directory:$1"
cd $1
sbt dependencyBrowseTreeHTML -batch