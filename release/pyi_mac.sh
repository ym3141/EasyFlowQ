#!/bin/sh

# delete and add folder
rm -r release/EasyFlowQ_release_mac/*
rm -r _temp/pyi_*
mkdir release/EasyFlowQ_release_mac/dmg

# get the current version number
_ver=$(python ./src/EasyFlowQ/__init__.py)

# get the git commit hash
git_commit=$(git rev-parse --short HEAD)

# package with pyinstaller and codesign
# conda activate easyflow_env
pyinstaller --noconfirm --distpath ./release/EasyFlowQ_release_mac/ --workpath ./_temp/ ./release/pyi_universal.spec -- --version $_ver
codesign -f -s YMa release/EasyFlowQ_release_mac/EasyFlowQ_MACOS.app

# Copy the app bundle to the dmg folder.
cp -r release/EasyFlowQ_release_mac/EasyFlowQ_MACOS.app release/EasyFlowQ_release_mac/dmg

# If the DMG already exists, delete it.
test -f release/EasyFlowQ_release_mac/EasyFlowQ_MACOS.dmg && rm release/EasyFlowQ_release_mac/EasyFlowQ_MACOS.dmg

create-dmg \
  --volname EasyFlowQ_MACOS_v${_ver}_${git_commit}.dmg \
  --icon EasyFlowQ_MACOS.app 120 120 \
  --app-drop-link 360 120 \
  release/EasyFlowQ_release_mac/EasyFlowQ_MACOS_v${_ver}_${git_commit}.dmg \
  release/EasyFlowQ_release_mac/dmg/