#!/usr/bin/env python3
"""
Test script to check audio devices
"""

import pyaudio

def test_audio_devices():
    try:
        p = pyaudio.PyAudio()
        print(f"Total devices: {p.get_device_count()}")
        print("\nAll devices:")
        print("-" * 50)
        
        input_devices = []
        
        for i in range(p.get_device_count()):
            try:
                info = p.get_device_info_by_index(i)
                name = info['name']
                input_channels = info['maxInputChannels']
                output_channels = info['maxOutputChannels']
                
                print(f"{i}: {name}")
                print(f"   Input channels: {input_channels}")
                print(f"   Output channels: {output_channels}")
                
                if input_channels > 0:
                    input_devices.append((i, name, input_channels))
                    
            except Exception as e:
                print(f"Error getting device {i}: {e}")
        
        print("\n" + "=" * 50)
        print("INPUT DEVICES (can be used for audio capture):")
        print("=" * 50)
        
        if input_devices:
            for device_id, name, channels in input_devices:
                print(f"{device_id}: {name} ({channels} channels)")
        else:
            print("No input devices found!")
            
        p.terminate()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_audio_devices() 