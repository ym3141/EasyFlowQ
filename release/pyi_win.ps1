# conda activate EasyFlowQ
$_ver = python ./src/EasyFlowQ/__init__.py

# delete the previous build
Remove-Item -Recurse -Force .\release\EasyFlowQ_release_win\

# build the app
pyinstaller --noconfirm --distpath .\release\EasyFlowQ_release_win\ --workpath .\_temp\ .\release\pyi_universal.spec -- --version $_ver

# wait 5 second for the process to finish
Start-Sleep -Seconds 5

# compress the build
Compress-Archive -Force -Path .\release\EasyFlowQ_release_win\EasyFlowQ_Bundle_v$_ver `
    -DestinationPath .\release\EasyFlowQ_release_win\EasyFlowQ_Win_v$_ver.zip
