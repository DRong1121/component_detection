echo "[INFO] Maven_Pom build script executing on directory:$1"
cd $1
mvn dependency:tree > maven_tree.txt