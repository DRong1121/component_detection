echo "[INFO] Cpan_Cli build script executing on directory:$1"
cd $1
cpanm . --showdeps > cpan_deps.txt