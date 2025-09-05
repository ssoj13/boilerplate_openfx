@echo off
set /p choice= "Enter commit message: "
echo Committing "%choice%"
git add -A . && git commit -a -m "%choice%" && git push --recurse-submodules=on-demand --set-upstream origin main


