echo "[INFO] Leiningen_Maven build script executing on directory:$1"
cd $1
lein pom
mvn dependency:tree > lein_maven_tree.txt