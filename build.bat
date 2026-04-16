@echo off
title Auto-Paster Builder
echo ========================================
echo   Auto-Paster EXE Builder
echo ========================================
echo.
echo [1/3] Cleaning up old builds...
if exist build rd /s /q build
if exist dist rd /s /q dist

echo.
echo [2/3] Updating dependencies...
pip install pyinstaller pyperclip uiautomation keyboard --quiet

echo.
echo [3/3] Building executable...
echo (This may take a minute or two)
pyinstaller --noconsole --onefile --uac-admin --version-file "version_info.txt" --name "auto-paster" auto_paster.py

echo.
echo ========================================
echo   BUILD COMPLETE!
echo   Location: dist/auto-paster.exe
echo ========================================
echo.
pause
