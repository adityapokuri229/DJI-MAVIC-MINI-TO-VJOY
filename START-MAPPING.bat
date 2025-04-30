@echo off
ECHO Reading properties.txt...

:: Initialize variables
SET serialPort=
SET buttonKey=

:: Read properties.txt
IF NOT EXIST properties.txt (
    ECHO Error: properties.txt not found.
    PAUSE
    EXIT /B 1
)

FOR /F "tokens=1,2 delims==" %%a IN (properties.txt) DO (
    IF "%%a"=="port" SET serialPort=%%b
    IF "%%a"=="buttonkey" SET buttonKey=%%b
)

:: Validate required inputs
IF "%serialPort%"=="" (
    ECHO Error: Port not specified in properties.txt.
    PAUSE
    EXIT /B 1
)

IF "%buttonKey%"=="" (
    ECHO Error: Button key not specified in properties.txt.
    PAUSE
    EXIT /B 1
)

:: Run the Python script
start python main.py -p %serialPort% -b1 %buttonKey%
exit