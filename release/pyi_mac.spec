# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['../main.py'],
             pathex=[],
             binaries=[],
             datas=[('../src/EasyFlowQ/uiDesigns/*', 'src/EasyFlowQ/uiDesigns/'), 
                    ('../src/EasyFlowQ/localSettings.default.json', 'src/EasyFlowQ/'),
                    ('../src/EasyFlowQ/uiDesigns/resource/PelatteIcon2.png', 'src/EasyFlowQ/uiDesigns/resource/')],
             hiddenimports=['qt_resource_rc', 'openpyxl', 'xlsxwritter', 'openpyxl.cell._writer'],
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
          name='main',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
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
               name='main')
app = BUNDLE(coll,
             name='EasyFlowQ_MACOS.app',
             icon=None,
             bundle_identifier=None)
