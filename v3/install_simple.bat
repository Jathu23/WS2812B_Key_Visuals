@echo off
echo Installing WS2812B LED Controller v3 Simple Dependencies...
echo.

echo Installing Python packages...
pip install pyserial==3.5
pip install pynput==1.7.6

echo.
echo Installation complete!
echo.
echo To run the simple GUI:
echo python guiv3_simple.py
echo.
pause 