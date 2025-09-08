@echo off
echo Building People Counter Application...
pyinstaller gui_app.spec

echo.
echo Build completed!
echo Executable is in the 'dist' folder: dist/People_Counter.exe
echo.
pause