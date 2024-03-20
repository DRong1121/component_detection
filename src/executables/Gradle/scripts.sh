echo "[INFO] Gradle build script executing on directory:$1"
cd $1
gradle dependencies > gradle_tree.txt