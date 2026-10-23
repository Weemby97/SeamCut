@echo off
cd /d "%~dp0"
call .venv\Scripts\activate
pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --name seamcut --icon assets\icon.ico --add-data "assets;assets" --collect-all numba --collect-all llvmlite main.py
echo.
echo Output: dist\seamcut\seamcut.exe
