@echo off
setlocal EnableExtensions
cd /d "%~dp0\.."

if not exist .venv (
  py -3.11 -m venv .venv || goto error
)
call .venv\Scripts\activate.bat || goto error
python -m pip install --upgrade pip || goto error
python -m pip install -r requirements.txt pytest pyinstaller || goto error
python -m pytest || goto error
python -m compileall svg_attribute_cleaner svg_attribute_cleaner.py || goto error
pyinstaller --onefile --windowed --name SvgAttributeCleaner --add-data "configs;configs" svg_attribute_cleaner.py || goto error
if not exist release mkdir release
powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Test-Path release/SvgAttributeCleaner-windows-x64.zip) { Remove-Item release/SvgAttributeCleaner-windows-x64.zip }; $stage='release/package'; if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }; New-Item -ItemType Directory -Path $stage, $stage/configs, $stage/scripts, $stage/output | Out-Null; Copy-Item dist/SvgAttributeCleaner.exe $stage/; Copy-Item README.md $stage/; Copy-Item configs/default.yaml $stage/configs/; Copy-Item scripts/run_gui.bat $stage/scripts/; Copy-Item output/.gitkeep $stage/output/; Compress-Archive -Path $stage/* -DestinationPath release/SvgAttributeCleaner-windows-x64.zip" || goto error

echo Build complete: dist\SvgAttributeCleaner.exe
echo Release zip: release\SvgAttributeCleaner-windows-x64.zip
pause
exit /b 0

:error
echo.
echo Build failed. Please review the error above.
pause
exit /b 1
