# conda activate EasyFlowQ
$_ver = python ./src/EasyFlowQ/__init__.py

# fetch remote for current branch
git fetch origin pyside6 2>$null

# check that pyside6 branch is up-to-date
$local = (& git rev-parse --short HEAD).Trim()
try {
    $remote = (& git rev-parse --short origin/pyside6).Trim()
} catch {
    $remote = $null
}

if (-not $remote) {
    Write-Error "No remote tracking branch found. Aborting."
    exit 1
}

if ($local -ne $remote) {
    Write-Error "Local HEAD ($local) is not at origin/pyside6 ($remote). Please pull/rebase before continuing."
    exit 1
}

Write-Output "Branch pyside6 is up-to-date at $local"

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
