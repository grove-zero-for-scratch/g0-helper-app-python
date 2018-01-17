# -*- mode: python -*-

block_cipher = None


a = Analysis(['win\\main.py'],
             pathex=['C:\\Users\\jy\\Desktop\\mygithub\\g0-helper-app-python\\g0_helper_app'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='Grove Zero Helper APP',
          debug=False,
          strip=False,
          upx=True,
          console=False, 
          icon ='icons.ico' )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='Grove Zero Helper APP')
