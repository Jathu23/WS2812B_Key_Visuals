@echo off
echo Installing WS2812B LED Controller v3 Dependencies...
echo.

echo Installing Python packages...
pip install pyserial==3.5
pip install pynput==1.7.6
pip install numpy==1.24.3
pip install sounddevice==0.4.6
pip install scipy==1.10.1
pip install psutil==5.9.5
pip install pywin32==306
pip install winotify==1.1.0

echo.
echo Installation complete!
echo.
echo To run the GUI:
echo python guiv3.py
echo.
pause 