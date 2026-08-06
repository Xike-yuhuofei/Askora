# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Askora Backend
打包 FastAPI 后端为独立可执行二进制
"""

block_cipher = None

a = Analysis(
    ['app/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('alembic', 'alembic'),
        ('alembic.ini', '.'),
        ('app/core', 'app/core'),
        ('app/api', 'app/api'),
        ('app/services', 'app/services'),
        ('app/engines', 'app/engines'),
        ('app/gateway', 'app/gateway'),
        ('app/models', 'app/models'),
        ('app/workers', 'app/workers'),
        ('app/utils', 'app/utils'),
    ],
    hiddenimports=[
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'sqlalchemy',
        'asyncpg',
        'aiosqlite',
        'redis',
        'aiokafka',
        'jieba',
        'pydantic',
        'structlog',
        'prometheus_client',
        'jwt',
        'passlib.handlers.bcrypt',
        'ebooklib',
        'pdfplumber',
        'docx',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PyQt5',
        'PyQt6',
        'wx',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='askora-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
