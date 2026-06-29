@echo off
setlocal
cd /d "%~dp0\.."
python svg_attribute_cleaner.py --gui
if errorlevel 1 pause
