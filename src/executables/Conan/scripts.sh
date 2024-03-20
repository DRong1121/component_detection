echo "[INFO] Conan build script executing on directory:$1"
cd $1
conan lock create ./conanfile.py