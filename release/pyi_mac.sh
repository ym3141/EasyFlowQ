#!/bin/sh

# delete and add folder
rm -r release/EasyFlowQ_release_mac/*
mkdir release/EasyFlowQ_release_mac/dmg

# package with pyinstaller and codesign
conda activate easyflow_env
pyinstaller --noconfirm --windowed --distpath ./release/EasyFlowQ_release_mac/ --workpath ./_temp/ ./release/pyi_mac.spec
codesign -f -s EasyFlowQ_YMa release/EasyFlowQ_release_mac/EasyFlowQ_MACOS.app

# Copy the app bundle to the dmg folder.
cp -r release/EasyFlowQ_release_mac/EasyFlowQ_MACOS.app release/EasyFlowQ_release_mac/dmg

# If the DMG already exists, delete it.
test -f release/EasyFlowQ_release_mac/EasyFlowQ_MACOS.dmg && rm release/EasyFlowQ_release_mac/EasyFlowQ_MACOS.dmg

create-dmg \
  --volname EasyFlowQ_MACOS.dmg \
  --icon EasyFlowQ_MACOS.app 120 120 \
  --app-drop-link 475 120 \
  release/EasyFlowQ_release_mac/EasyFlowQ_MACOS.dmg \
  release/EasyFlowQ_release_mac/dmg/