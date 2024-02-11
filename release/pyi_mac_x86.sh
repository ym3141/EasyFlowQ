#!/bin/sh

# delete and add folder
rm -r release/EasyFlowQ_release_mac_x86/*
mkdir release/EasyFlowQ_release_mac_x86/dmg

# package with pyinstaller and codesign
# conda activate easyflow_env
pyinstaller --noconfirm --distpath ./release/EasyFlowQ_release_mac_x86/ --workpath ./_temp/ ./release/pyi_mac.spec
mv ./release/EasyFlowQ_release_mac_x86/EasyFlowQ_MACOS.app ./release/EasyFlowQ_release_mac_x86/EasyFlowQ_MACOS_x86.app
codesign -f -s EasyFlowQ_YMa release/EasyFlowQ_release_mac_x86/EasyFlowQ_MACOS_x86.app

# Copy the app bundle to the dmg folder.
cp -r release/EasyFlowQ_release_mac_x86/EasyFlowQ_MACOS_x86.app release/EasyFlowQ_release_mac_x86/dmg

# If the DMG already exists, delete it.
test -f release/EasyFlowQ_release_mac_x86/EasyFlowQ_MACOS_x86.dmg && rm release/EasyFlowQ_release_mac_x86/EasyFlowQ_MACOS_x86.dmg

create-dmg \
  --volname EasyFlowQ_MACOS_x86.dmg \
  --icon EasyFlowQ_MACOS_x86.app 120 120 \
  --app-drop-link 360 120 \
  release/EasyFlowQ_release_mac_x86/EasyFlowQ_MACOS_x86.dmg \
  release/EasyFlowQ_release_mac_x86/dmg/