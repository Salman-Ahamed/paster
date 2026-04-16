@echo off
title Auto-Paster Builder
echo ========================================
echo   Auto-Paster EXE Builder
echo ========================================
echo.
echo [1/2] Updating dependencies...
pip install pyinstaller pyperclip uiautomation keyboard --quiet

echo.
echo [2/2] Building executable...
echo (This may take a minute or two)
pyinstaller --noconsole --onefile auto_paster.py

echo.
echo ========================================
echo   BUILD COMPLETE!
echo   Location: dist/auto_paster.exe
echo ========================================
echo.
pause
