echo "[INFO] Go_Mod_Cli build script executing on directory:$1"
cd $1
go list -m -mod=readonly all > gomod_list.txt