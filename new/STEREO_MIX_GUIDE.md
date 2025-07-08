# How to Enable Stereo Mix for System Audio Capture

Stereo Mix allows you to capture system audio (music, videos, games) instead of just microphone input.

## Method 1: Enable Stereo Mix in Windows

1. **Right-click on the speaker icon** in the system tray
2. **Select "Open Sound settings"**
3. **Click on "Sound Control Panel"** (under Related Settings)
4. **Go to the "Recording" tab**
5. **Right-click in the empty area** and select **"Show Disabled Devices"**
6. **Right-click on "Stereo Mix"** and select **"Enable"**
7. **Right-click on "Stereo Mix"** again and select **"Set as Default Device"**

## Method 2: If Stereo Mix is not visible

1. **Open Device Manager**
2. **Expand "Audio inputs and outputs"**
3. **Right-click on your audio device** (Realtek, etc.)
4. **Select "Update driver"**
5. **Restart your computer**
6. **Follow Method 1 above**

## Method 3: Alternative - Use VB-CABLE

If Stereo Mix is not available:

1. **Download VB-CABLE Virtual Audio Device** from: https://vb-audio.com/Cable/
2. **Install VB-CABLE**
3. **Set VB-CABLE as your default playback device**
4. **Use VB-CABLE as your audio input in the application**

## Testing Stereo Mix

1. **Play some music or video**
2. **Open the LED Controller application**
3. **Go to the Audio tab**
4. **Select "Stereo Mix" from the device list**
5. **Enable Audio Visualization**
6. **The LEDs should now respond to your system audio!**

## Troubleshooting

- **No audio detected**: Make sure system audio is playing
- **Low volume**: Increase the audio sensitivity slider
- **Still not working**: Try restarting the application after enabling Stereo Mix
- **Permission issues**: Check Windows privacy settings for microphone access

## Recommended Audio Settings

- **Audio Sensitivity**: 50-80 (adjust based on your audio levels)
- **Audio Mode**: Try "Spectrum Analyzer" or "Audio Wave" for best results
- **System Volume**: Keep at 50-70% for best detection 