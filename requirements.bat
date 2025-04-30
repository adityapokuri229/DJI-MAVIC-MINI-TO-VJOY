@echo off
echo Installing required Python packages...

pip install pyserial==3.4
pip install pyvjoy==1.0.1
pip install keyboard==0.13.5

echo.
echo Press any key to exit.
pause >nul