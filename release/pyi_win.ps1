# conda activate EasyFlowQ
$_ver = python ./src/EasyFlowQ/__init__.py

pyinstaller --noconfirm --distpath .\release\EasyFlowQ_release_win\ --workpath .\_temp\ .\release\pyi_universal.spec -- --version $_ver
Compress-Archive -Path .\release\EasyFlowQ_release_win\EasyFlowQ_Bundle_v$_ver `
    -DestinationPath .\release\EasyFlowQ_release_win\EasyFlowQ_Win_v$_ver.zip
