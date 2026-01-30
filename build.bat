@echo off
echo Starting build process...
pip install pyinstaller -r requirements.txt
pyinstaller --noconsole --onefile --name "GoldPriceSaver" main.py
echo.
echo Build finished! 
echo The executable is in the 'dist' folder.
echo To use it as a screensaver:
echo 1. Rename 'dist/GoldPriceSaver.exe' to 'GoldPriceSaver.scr'
echo 2. Right-click the .scr file and select 'Install'
pause
