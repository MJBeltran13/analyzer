@echo off
echo Creating desktop shortcut for Modern Antenna Analyzer...

REM Get the current directory
set "CURRENT_DIR=%~dp0"
set "PYTHON_PATH=python.exe"
set "SCRIPT_PATH=%CURRENT_DIR%analyzer.py"

REM Create VBS script to run the analyzer
echo Set WshShell = CreateObject("WScript.Shell") > "%TEMP%\run_analyzer.vbs"
echo Set shortcut = WshShell.CreateShortcut("%CURRENT_DIR%Antenna Analyzer.lnk") >> "%TEMP%\run_analyzer.vbs"
echo shortcut.TargetPath = "%PYTHON_PATH%" >> "%TEMP%\run_analyzer.vbs"
echo shortcut.Arguments = "%SCRIPT_PATH%" >> "%TEMP%\run_analyzer.vbs"
echo shortcut.WorkingDirectory = "%CURRENT_DIR%" >> "%TEMP%\run_analyzer.vbs"
echo shortcut.Description = "Modern Antenna Analyzer" >> "%TEMP%\run_analyzer.vbs"
echo shortcut.IconLocation = "%PYTHON_PATH%,0" >> "%TEMP%\run_analyzer.vbs"
echo shortcut.Save >> "%TEMP%\run_analyzer.vbs"

REM Run the VBS script
cscript //nologo "%TEMP%\run_analyzer.vbs"

REM Clean up
del "%TEMP%\run_analyzer.vbs"

echo.
echo ✅ Shortcut created successfully in this folder!
echo You can now double-click "Antenna Analyzer.lnk" to run the application.
pause
