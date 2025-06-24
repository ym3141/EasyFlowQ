# conda activate EasyFlowQ
$_ver = python ./src/EasyFlowQ/__init__.py

# get current git commit hash
$git_commit = git rev-parse --short HEAD
if ($git_commit -eq $null) {
    echo "Git commit hash not found. Using 'unknown' as version."
    $git_commit = "unknown"
}

# delete the previous build
if (Test-Path .\release\EasyFlowQ_release_win\) {
    rm -r .\release\EasyFlowQ_release_win\*
} else {
    mkdir .\release\EasyFlowQ_release_win\
}

# build the app
$versionString = "$_ver" + "_" + $git_commit

$pyinstallerArgs = @(
    "--noconfirm"
    "--distpath", ".\release\EasyFlowQ_release_win\"
    "--workpath", ".\_temp\"
    ".\release\pyi_universal.spec"
    "--", "--version", $_ver
)

pyinstaller @pyinstallerArgs

# wait 5 second for the process to finish
Start-Sleep -Seconds 10

# compress the build
Compress-Archive -Force -Path .\release\EasyFlowQ_release_win\EasyFlowQ_Bundle_v$_ver `
    -DestinationPath .\release\EasyFlowQ_release_win\EasyFlowQ_Win_v$versionString.zip

# start the easfylowq app
Start-Process -FilePath .\release\EasyFlowQ_release_win\EasyFlowQ_Bundle_v$_ver\EasyFlowQ_v$_ver.exe
