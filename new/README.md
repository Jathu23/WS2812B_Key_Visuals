# Arduino LED Strip Controller

A Python GUI application for controlling WS2812B LED strips via Arduino with real-time keyboard typing visualization, audio reactivity, and notification alerts.

## Features

- **Real-time Keyboard Visualization**: LED animations triggered by keyboard input (with automatic timeout)
- **Audio Reactivity**: LED patterns that respond to audio input
- **Notification Alerts**: Visual alerts for system notifications
- **Idle Animations**: Custom animations when the system is idle
- **Multiple Animation Modes**: Various effects for each feature
- **Profile Management**: Save and load different configurations
- **Serial Communication**: Direct control of Arduino via USB
- **Smart Keyboard Debouncing**: Prevents continuous animation triggers

## Requirements

- Python 3.7 or higher
- Arduino Nano or compatible board
- WS2812B LED strip
- Windows 10/11 (for notification monitoring)

## Installation

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   
   Or run the installation script:
   ```bash
   install.bat
   ```

2. **Upload Arduino Code**:
   - Open `ledcontroller/ledcontroller.ino` in Arduino IDE
   - Install the FastLED library (Tools > Manage Libraries > search "FastLED")
   - Select your Arduino board and port
   - Upload the code

3. **Hardware Setup**:
   - Connect WS2812B LED strip to Arduino pin 6
   - Connect power supply (5V) to LED strip
   - Connect Arduino to computer via USB

## Usage

1. **Run the Application**:
   ```bash
   python gui.py
   ```

2. **Connect to Arduino**:
   - Select the correct COM port
   - Click "Connect"

3. **Configure Features**:
   - **Keyboard Tab**: Enable typing visualization and select animation mode
   - **Audio Tab**: Enable audio reactivity and select input device
   - **Notifications Tab**: Configure notification alerts
   - **Idle Tab**: Set idle timeout and animation mode
   - **Settings Tab**: Save/load profiles and configure advanced options

## Animation Modes

### Keyboard Modes
- **Center Spread**: Animation spreads from center outward
- **Random Blink**: Random LED blinking
- **Single Color Blink**: All LEDs blink in same color
- **Wave Effect**: Color wave animation
- **Typing Trail**: Moving trail effect

**Keyboard Behavior**:
- Animations trigger only when keys are pressed
- Each key press creates a single animation cycle
- Animation duration is configurable (0.5 to 3.0 seconds)
- Automatic return to idle mode after animation completes
- Debouncing prevents multiple rapid triggers

### Audio Modes
- **Center Out**: Audio level spreads from center with dynamic colors
- **Random Colors**: Random color flashes based on audio intensity
- **Single Color**: Dynamic color based on dominant frequency
- **VU Meter**: Traditional volume unit meter with peak indicator
- **Spectrum Analyzer**: 8-band frequency analysis with color mapping
- **Audio Wave**: Wave pattern that responds to audio level and speed
- **Audio Pulse**: Pulsing effect triggered by audio beats
- **Center Bars**: Enhanced center bars with smooth gradients and sparkle effects

**Audio Features**:
- **System Audio Support**: Use Stereo Mix to capture music, videos, games
- **Enhanced Frequency Analysis**: 8 logarithmic frequency bands for better music response
- **Dynamic Color Mapping**: Colors change based on frequency content
- **Improved Sensitivity**: Better detection of system audio levels
- **Real-time Processing**: 20 FPS audio processing for smooth animations

### Idle Modes
- **Knight Rider**: Classic scanning light effect
- **Rainbow**: Smooth rainbow animation
- **Sand Clock**: Falling sand effect
- **Breathing**: Gentle breathing light effect
- **Fire**: Fire-like flickering effect

## Audio Setup

### For System Audio (Music, Videos, Games)

To capture system audio instead of microphone input:

1. **Enable Stereo Mix** (see `STEREO_MIX_GUIDE.md` for detailed instructions)
2. **Select "Stereo Mix"** from the audio device dropdown
3. **Play music or video** on your computer
4. **Enable Audio Visualization** in the Audio tab
5. **Adjust sensitivity** as needed

### For Microphone Input

1. **Select your microphone** from the audio device dropdown
2. **Speak or make sounds** near the microphone
3. **Enable Audio Visualization**
4. **Adjust sensitivity** for best response

### Recommended Settings

- **Audio Sensitivity**: 50-80 (higher for quiet sources)
- **Audio Mode**: 
  - **Spectrum Analyzer**: Best for music with clear frequency separation
  - **Audio Wave**: Good for ambient music and continuous audio
  - **Audio Pulse**: Great for rhythmic music and beats
  - **Center Bars**: Beautiful center-expanding bars with gradients and sparkles
  - **VU Meter**: Simple volume visualization

## Troubleshooting

### Common Issues

1. **"No audio devices available"**:
   - Audio devices are now automatically detected on startup
   - Use the "Refresh Audio Devices" button if needed
   - Check microphone permissions in Windows settings
   - Try different audio input devices
   - Restart the application if issues persist

2. **Connection failed**:
   - Verify Arduino is connected and port is correct
   - Check if Arduino code is uploaded successfully
   - Try different USB cable

3. **Audio not working**:
   - Select correct audio input device from the dropdown
   - Check system audio settings and microphone permissions
   - Adjust audio sensitivity slider
   - Ensure the selected device is not being used by another application

4. **Keyboard monitoring not working**:
   - Grant keyboard permissions if prompted
   - Check if antivirus is blocking the application
   - Restart the application

### Debug Mode

Enable debug logging in the Settings tab to see detailed error messages and communication logs.

## File Structure

```
new/
├── gui.py                 # Main GUI application
├── ledcontroller/
│   └── ledcontroller.ino  # Arduino code
├── requirements.txt       # Python dependencies
├── install.bat           # Installation script
└── README.md             # This file
```

## Technical Details

- **Serial Communication**: 115200 baud rate
- **LED Configuration**: 60 LEDs, WS2812B, GRB color order
- **Audio Processing**: 44.1kHz, 16-bit, mono
- **Update Rate**: 50 FPS for smooth animations

## License

This project is open source and available under the MIT License. 