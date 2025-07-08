#!/usr/bin/env python3
"""
Test script to verify audio sensitivity and levels
"""

import numpy as np
import pyaudio
import time
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_audio_sensitivity():
    """Test audio sensitivity with different devices"""
    try:
        p = pyaudio.PyAudio()
        print("Audio Sensitivity Test")
        print("=" * 50)
        
        # List all input devices
        input_devices = []
        for i in range(p.get_device_count()):
            try:
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    input_devices.append((i, info['name']))
                    print(f"{i}: {info['name']}")
            except Exception as e:
                print(f"Error getting device {i}: {e}")
        
        if not input_devices:
            print("No input devices found!")
            return
        
        print(f"\nFound {len(input_devices)} input devices")
        print("\nTesting each device for 5 seconds...")
        print("Make some noise or play music while testing!")
        
        for device_id, device_name in input_devices:
            print(f"\n--- Testing Device {device_id}: {device_name} ---")
            
            try:
                # Open audio stream
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=44100,
                    input=True,
                    input_device_index=device_id,
                    frames_per_buffer=1024
                )
                
                max_level = 0
                samples = 0
                
                # Test for 5 seconds
                for _ in range(50):  # 5 seconds at 10 samples per second
                    try:
                        data = stream.read(1024, exception_on_overflow=False)
                        audio_data = np.frombuffer(data, dtype=np.int16)
                        
                        # Calculate levels
                        peak_level = np.max(np.abs(audio_data))
                        rms = np.sqrt(np.mean(audio_data**2))
                        combined_level = (peak_level * 0.3 + rms * 0.7)
                        
                        # Test different sensitivity levels
                        sensitivity_50 = int(combined_level * 50 / 50)
                        sensitivity_100 = int(combined_level * 100 / 50)
                        
                        max_level = max(max_level, sensitivity_100)
                        samples += 1
                        
                        # Show progress
                        if samples % 10 == 0:
                            print(f"  Sample {samples}: Level={sensitivity_100}/255 (Sens50={sensitivity_50}, Sens100={sensitivity_100})")
                        
                        time.sleep(0.1)
                        
                    except Exception as e:
                        print(f"  Error reading audio: {e}")
                        break
                
                # Close stream
                stream.stop_stream()
                stream.close()
                
                # Show results
                if samples > 0:
                    if max_level > 20:
                        print(f"  ✅ GOOD: Max level = {max_level}/255")
                        print(f"  📊 Sensitivity 50: ~{max_level//2}/255")
                        print(f"  📊 Sensitivity 100: ~{max_level}/255")
                    elif max_level > 5:
                        print(f"  ⚠️  WEAK: Max level = {max_level}/255")
                        print(f"  💡 Try increasing system volume or sensitivity")
                    else:
                        print(f"  ❌ VERY WEAK: Max level = {max_level}/255")
                        print(f"  💡 Check audio source and device settings")
                else:
                    print(f"  ❌ NO AUDIO: No samples captured")
                
            except Exception as e:
                print(f"  ❌ ERROR: {e}")
        
        p.terminate()
        
        print("\n" + "=" * 50)
        print("Test Complete!")
        print("\nRecommendations:")
        print("• Use devices with GOOD or WEAK results")
        print("• For WEAK devices, increase system volume")
        print("• For VERY WEAK devices, try different audio source")
        print("• Stereo Mix is best for system audio capture")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_audio_sensitivity() 