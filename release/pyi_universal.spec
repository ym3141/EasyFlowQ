# -*- mode: python ; coding: utf-8 -*-
from sys import platform
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--version", action="store", default="0.0")
options = parser.parse_args()
_ver = options.version

exe_name = "EasyFlowQ_v{0}".format(_ver)
bundle_name = "EasyFlowQ_Bundle_v{0}".format(_ver)

if platform == 'darwin':
    exe_console = False
    hidden_imports = ['qt_resource_rc', 'openpyxl', 'xlsxwritter', 'openpyxl.cell._writer']
elif platform == 'win32':
    exe_console = True
    hidden_imports = ['xlsxwritter', 'pyside6-uic']

block_cipher = None

a = Analysis(['../main.py'],
             pathex=[],
             binaries=[],
             datas=[('../src/EasyFlowQ/uiDesigns/*', 'src/EasyFlowQ/uiDesigns/'), 
                    ('../src/EasyFlowQ/localSettings.default.json', 'src/EasyFlowQ/'),
                    ('../src/EasyFlowQ/uiDesigns/resource/PelatteIcon2.png', 'src/EasyFlowQ/uiDesigns/resource/')],
             hiddenimports=hidden_imports,
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts, 
          [],
          exclude_binaries=True,
          name=exe_name,
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=exe_console,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas, 
               strip=False,
               upx=True,
               upx_exclude=[],
               name=bundle_name)

if platform=='darwin':
    app = BUNDLE(coll,
                name='EasyFlowQ_MACOS.app',
                version=_ver,
                icon=None,
                bundle_identifier=None)

