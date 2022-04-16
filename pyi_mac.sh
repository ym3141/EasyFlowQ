#!/bin/sh
pyinstaller --noconfirm --windowed --distpath ./EasyFlowQ_release_mac/ --workpath ./_temp/ ./pyi_mac.spec
codesign -f -s EasyFlowQ_YMa EasyFlowQ_release_mac/EasyFlowQ_mac.app