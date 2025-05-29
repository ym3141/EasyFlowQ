# conda activate EasyFlowQ
$_ver = python ./src/EasyFlowQ/__init__.py

# get current git commit hash
$git_commit = git rev-parse --short HEAD
if ($git_commit -eq $null) {
    Write-Host "Git commit hash not found. Using 'unknown' as version."
    $git_commit = "unknown"
}

# delete the previous build
Remove-Item -Recurse -Force .\release\EasyFlowQ_release_win\

# build the app
$versionString = "$_ver" + "_bld_" + $git_commit
$pyinstallerArgs = @(
    "--noconfirm"
    "--distpath", ".\release\EasyFlowQ_release_win\"
    "--workpath", ".\_temp\"
    ".\release\pyi_universal.spec"
    "--version", $versionString
)
pyinstaller @pyinstallerArgs

# wait 5 second for the process to finish
Start-Sleep -Seconds 5

# compress the build
Compress-Archive -Force -Path .\release\EasyFlowQ_release_win\EasyFlowQ_Bundle_v$versionString `
    -DestinationPath .\release\EasyFlowQ_release_win\EasyFlowQ_Win_v$versionString.zip
