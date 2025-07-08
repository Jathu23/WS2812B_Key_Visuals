import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import time
import json
import os
import pyaudio
import numpy as np
from pynput import keyboard
import queue
import win10toast
import psutil
import sys

class LEDController:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Arduino LED Strip Controller")
        self.root.geometry("800x900")
        self.root.resizable(True, True)
        
        # Serial connection
        self.serial_connection = None
        self.connected = False
        
        # Audio setup
        self.audio_stream = None
        self.audio_enabled = False
        self.pyaudio_instance = None
        
        # Keyboard monitoring
        self.keyboard_listener = None
        self.keyboard_enabled = False
        self.last_key_time = 0
        self.keyboard_debounce_time = 0.1  # 100ms debounce
        self.last_keyboard_trigger = 0
        
        # Notification monitoring
        self.notification_enabled = True
        
        # Threading
        self.running = True
        self.command_queue = queue.Queue()
        
        # Settings
        self.settings = self.load_settings()
        
        self.setup_ui()
        self.setup_audio_system()
        self.start_background_threads()
        
        # Window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_ui(self):
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Connection Tab
        self.setup_connection_tab(notebook)
        
        # Keyboard Tab
        self.setup_keyboard_tab(notebook)
        
        # Audio Tab  
        self.setup_audio_tab(notebook)
        
        # Notifications Tab
        self.setup_notifications_tab(notebook)
        
        # Idle Tab
        self.setup_idle_tab(notebook)
        
        # Settings Tab
        self.setup_settings_tab(notebook)
        
    def setup_connection_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Connection")
        
        # Connection section
        conn_frame = ttk.LabelFrame(frame, text="Serial Connection", padding=10)
        conn_frame.pack(fill=tk.X, pady=5)
        
        # Port selection
        ttk.Label(conn_frame, text="Select Port:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var, width=30)
        self.port_combo.grid(row=0, column=1, padx=5, pady=2)
        
        # Refresh and Connect buttons
        ttk.Button(conn_frame, text="Refresh", command=self.refresh_ports).grid(row=0, column=2, padx=5)
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.grid(row=1, column=1, pady=10)
        
        # Connection status
        self.status_var = tk.StringVar(value="Disconnected")
        self.status_label = ttk.Label(conn_frame, textvariable=self.status_var, foreground="red")
        self.status_label.grid(row=1, column=0, sticky=tk.W)
        
        # System Control
        system_frame = ttk.LabelFrame(frame, text="System Control", padding=10)
        system_frame.pack(fill=tk.X, pady=5)
        
        self.system_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(system_frame, text="System Enabled", 
                       variable=self.system_enabled_var,
                       command=self.toggle_system).pack(anchor=tk.W)
        
        # Brightness control
        ttk.Label(system_frame, text="Brightness:").pack(anchor=tk.W, pady=(10,0))
        self.brightness_var = tk.IntVar(value=200)
        brightness_scale = tk.Scale(system_frame, from_=10, to=255, orient=tk.HORIZONTAL,
                                  variable=self.brightness_var, command=self.set_brightness)
        brightness_scale.pack(fill=tk.X, pady=2)
        
        # Initialize port list
        self.refresh_ports()
        
    def setup_keyboard_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Keyboard")
        
        # Enable/Disable
        ctrl_frame = ttk.LabelFrame(frame, text="Keyboard Monitoring", padding=10)
        ctrl_frame.pack(fill=tk.X, pady=5)
        
        self.keyboard_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(ctrl_frame, text="Enable Keyboard Monitoring",
                       variable=self.keyboard_enabled_var,
                       command=self.toggle_keyboard_monitoring).pack(anchor=tk.W)
        
        # Animation Modes
        modes_frame = ttk.LabelFrame(frame, text="Animation Modes", padding=10)
        modes_frame.pack(fill=tk.X, pady=5)
        
        self.keyboard_mode_var = tk.IntVar(value=0)
        modes = [
            ("Center Spread", 0),
            ("Random Blink", 1),
            ("Single Color Blink", 2),
            ("Wave Effect", 3),
            ("Typing Trail", 4)
        ]
        
        for text, value in modes:
            ttk.Radiobutton(modes_frame, text=text, variable=self.keyboard_mode_var,
                           value=value, command=self.set_keyboard_mode).pack(anchor=tk.W)
        
        # Animation Duration
        duration_frame = ttk.LabelFrame(frame, text="Animation Duration", padding=10)
        duration_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(duration_frame, text="Animation Duration (seconds):").pack(anchor=tk.W)
        self.keyboard_duration_var = tk.IntVar(value=1)
        duration_scale = tk.Scale(duration_frame, from_=0.5, to=3.0, resolution=0.1, orient=tk.HORIZONTAL,
                                variable=self.keyboard_duration_var, command=self.set_keyboard_duration)
        duration_scale.pack(fill=tk.X, pady=2)
        
        # Status
        status_frame = ttk.LabelFrame(frame, text="Status", padding=10)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.kb_status_var = tk.StringVar(value="Monitoring: Disabled")
        ttk.Label(status_frame, textvariable=self.kb_status_var).pack(anchor=tk.W)
        
        self.last_key_var = tk.StringVar(value="Last Key: None")
        ttk.Label(status_frame, textvariable=self.last_key_var).pack(anchor=tk.W)
        
    def setup_audio_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Audio")
        
        # Enable/Disable
        ctrl_frame = ttk.LabelFrame(frame, text="Audio Visualization", padding=10)
        ctrl_frame.pack(fill=tk.X, pady=5)
        
        self.audio_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(ctrl_frame, text="Enable Audio Visualization",
                       variable=self.audio_enabled_var,
                       command=self.toggle_audio_visualization).pack(anchor=tk.W)
        
        # Audio device selection
        ttk.Label(ctrl_frame, text="Audio Device:").pack(anchor=tk.W, pady=(10,0))
        self.audio_device_var = tk.StringVar()
        self.audio_device_combo = ttk.Combobox(ctrl_frame, textvariable=self.audio_device_var)
        self.audio_device_combo.pack(fill=tk.X, pady=2)
        
        # Refresh button for audio devices
        ttk.Button(ctrl_frame, text="Refresh Audio Devices", 
                  command=self.refresh_audio_devices).pack(anchor=tk.W, pady=5)
        
        # Test audio button
        ttk.Button(ctrl_frame, text="Test Audio Level", 
                  command=self.test_audio_level).pack(anchor=tk.W, pady=5)
        
        # Animation Modes
        modes_frame = ttk.LabelFrame(frame, text="Visualization Modes", padding=10)
        modes_frame.pack(fill=tk.X, pady=5)
        
        self.audio_mode_var = tk.IntVar(value=0)
        modes = [
            ("Center Out", 0),
            ("Random Colors", 1),
            ("Single Color", 2),
            ("VU Meter", 3),
            ("Spectrum Analyzer", 4),
            ("Audio Wave", 5),
            ("Audio Pulse", 6),
            ("Center Bars", 7)
        ]
        
        for text, value in modes:
            ttk.Radiobutton(modes_frame, text=text, variable=self.audio_mode_var,
                           value=value, command=self.set_audio_mode).pack(anchor=tk.W)
        
        # Sensitivity
        sens_frame = ttk.LabelFrame(frame, text="Sensitivity", padding=10)
        sens_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(sens_frame, text="Audio Sensitivity:").pack(anchor=tk.W)
        self.audio_sensitivity_var = tk.IntVar(value=50)
        sensitivity_scale = tk.Scale(sens_frame, from_=1, to=100, orient=tk.HORIZONTAL,
                                   variable=self.audio_sensitivity_var)
        sensitivity_scale.pack(fill=tk.X, pady=2)
        
        # Status
        status_frame = ttk.LabelFrame(frame, text="Status", padding=10)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.audio_status_var = tk.StringVar(value="Audio: Disabled")
        ttk.Label(status_frame, textvariable=self.audio_status_var).pack(anchor=tk.W)
        
        self.audio_level_var = tk.StringVar(value="Level: 0")
        ttk.Label(status_frame, textvariable=self.audio_level_var).pack(anchor=tk.W)
        
    def setup_notifications_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Notifications")
        
        # Enable/Disable
        ctrl_frame = ttk.LabelFrame(frame, text="Notification Monitoring", padding=10)
        ctrl_frame.pack(fill=tk.X, pady=5)
        
        self.notification_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(ctrl_frame, text="Enable Notification Alerts",
                       variable=self.notification_enabled_var,
                       command=self.toggle_notifications).pack(anchor=tk.W)
        
        # Animation Modes
        modes_frame = ttk.LabelFrame(frame, text="Alert Animations", padding=10)
        modes_frame.pack(fill=tk.X, pady=5)
        
        self.notification_mode_var = tk.IntVar(value=1)
        modes = [
            ("Double Blink", 1),
            ("Center to Ends", 2),
            ("Strobe Effect", 3)
        ]
        
        for text, value in modes:
            ttk.Radiobutton(modes_frame, text=text, variable=self.notification_mode_var,
                           value=value, command=self.set_notification_mode).pack(anchor=tk.W)
        
        # Test buttons
        test_frame = ttk.LabelFrame(frame, text="Test Notifications", padding=10)
        test_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(test_frame, text="Test Notification", 
                  command=self.test_notification).pack(side=tk.LEFT, padx=5)
        
        # Monitored applications
        apps_frame = ttk.LabelFrame(frame, text="Monitor Applications", padding=10)
        apps_frame.pack(fill=tk.X, pady=5)
        
        # Common apps checkboxes
        self.monitor_apps = {}
        apps = ["Discord", "WhatsApp", "Telegram", "Slack", "Outlook", "Chrome", "Firefox"]
        
        for i, app in enumerate(apps):
            var = tk.BooleanVar(value=True)
            self.monitor_apps[app] = var
            ttk.Checkbutton(apps_frame, text=app, variable=var).grid(
                row=i//3, column=i%3, sticky=tk.W, padx=5, pady=2)
        
        # Status
        status_frame = ttk.LabelFrame(frame, text="Status", padding=10)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.notif_status_var = tk.StringVar(value="Monitoring: Enabled")
        ttk.Label(status_frame, textvariable=self.notif_status_var).pack(anchor=tk.W)
        
        self.last_notif_var = tk.StringVar(value="Last Alert: None")
        ttk.Label(status_frame, textvariable=self.last_notif_var).pack(anchor=tk.W)
        
    def setup_idle_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Idle Mode")
        
        # Enable/Disable
        ctrl_frame = ttk.LabelFrame(frame, text="Idle Animation", padding=10)
        ctrl_frame.pack(fill=tk.X, pady=5)
        
        self.idle_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(ctrl_frame, text="Enable Idle Animations",
                       variable=self.idle_enabled_var,
                       command=self.toggle_idle_mode).pack(anchor=tk.W)
        
        # Timeout setting
        ttk.Label(ctrl_frame, text="Idle Timeout (seconds):").pack(anchor=tk.W, pady=(10,0))
        self.idle_timeout_var = tk.IntVar(value=30)
        timeout_scale = tk.Scale(ctrl_frame, from_=10, to=300, orient=tk.HORIZONTAL,
                               variable=self.idle_timeout_var, command=self.set_idle_timeout)
        timeout_scale.pack(fill=tk.X, pady=2)
        
        # Animation Modes
        modes_frame = ttk.LabelFrame(frame, text="Idle Animations", padding=10)
        modes_frame.pack(fill=tk.X, pady=5)
        
        self.idle_mode_var = tk.IntVar(value=0)
        modes = [
            ("Knight Rider", 0),
            ("Rainbow", 1),
            ("Sand Clock", 2),
            ("Breathing", 3),
            ("Fire Effect", 4)
        ]
        
        for text, value in modes:
            ttk.Radiobutton(modes_frame, text=text, variable=self.idle_mode_var,
                           value=value, command=self.set_idle_mode).pack(anchor=tk.W)
        
        # Status
        status_frame = ttk.LabelFrame(frame, text="Status", padding=10)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.idle_status_var = tk.StringVar(value="Idle Mode: Enabled")
        ttk.Label(status_frame, textvariable=self.idle_status_var).pack(anchor=tk.W)
        
    def setup_settings_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Settings")
        
        # Profile management
        profile_frame = ttk.LabelFrame(frame, text="Profile Management", padding=10)
        profile_frame.pack(fill=tk.X, pady=5)
        
        profile_btn_frame = ttk.Frame(profile_frame)
        profile_btn_frame.pack(fill=tk.X)
        
        ttk.Button(profile_btn_frame, text="Save Profile", 
                  command=self.save_profile).pack(side=tk.LEFT, padx=5)
        ttk.Button(profile_btn_frame, text="Load Profile", 
                  command=self.load_profile).pack(side=tk.LEFT, padx=5)
        ttk.Button(profile_btn_frame, text="Reset to Default", 
                  command=self.reset_settings).pack(side=tk.LEFT, padx=5)
        
        # Advanced settings
        advanced_frame = ttk.LabelFrame(frame, text="Advanced Settings", padding=10)
        advanced_frame.pack(fill=tk.X, pady=5)
        
        # Auto-connect
        self.auto_connect_var = tk.BooleanVar(value=self.settings.get('auto_connect', False))
        ttk.Checkbutton(advanced_frame, text="Auto-connect on startup",
                       variable=self.auto_connect_var,
                       command=self.save_settings).pack(anchor=tk.W)
        
        # Start minimized
        self.start_minimized_var = tk.BooleanVar(value=self.settings.get('start_minimized', False))
        ttk.Checkbutton(advanced_frame, text="Start minimized to system tray",
                       variable=self.start_minimized_var,
                       command=self.save_settings).pack(anchor=tk.W)
        
        # Debug mode
        self.debug_mode_var = tk.BooleanVar(value=self.settings.get('debug_mode', False))
        ttk.Checkbutton(advanced_frame, text="Enable debug logging",
                       variable=self.debug_mode_var,
                       command=self.save_settings).pack(anchor=tk.W)
        
        # About section
        about_frame = ttk.LabelFrame(frame, text="About", padding=10)
        about_frame.pack(fill=tk.X, pady=5)
        
        about_text = """Arduino LED Strip Controller v1.0
        
Features:
• Real-time keyboard typing visualization
• Audio-reactive LED animations
• Smart notification alerts
• Customizable idle animations
• Multiple animation modes for each feature
• Profile management and settings

Created for Arduino Nano + WS2812B LED strips"""
        
        ttk.Label(about_frame, text=about_text, justify=tk.LEFT).pack(anchor=tk.W)
        
    def setup_audio_system(self):
        """Initialize audio system components"""
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            # Refresh audio devices after PyAudio is initialized
            self.refresh_audio_devices()
        except Exception as e:
            print(f"Failed to initialize PyAudio: {e}")
            self.pyaudio_instance = None
        
    # Serial Communication Methods
    def refresh_ports(self):
        ports = [port.device + " - " + port.description for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.current(0)
            
    def toggle_connection(self):
        if not self.connected:
            self.connect_to_arduino()
        else:
            self.disconnect_from_arduino()
            
    def connect_to_arduino(self):
        selected_port = self.port_var.get()
        if not selected_port:
            messagebox.showerror("Error", "Please select a port")
            return
            
        port_name = selected_port.split(" - ")[0]
        
        try:
            self.serial_connection = serial.Serial(port_name, 115200, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
            
            self.connected = True
            self.status_var.set("Connected")
            self.status_label.config(foreground="green")
            self.connect_btn.config(text="Disconnect")
            
            # Send initial configuration
            self.send_all_settings()
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
            
    def disconnect_from_arduino(self):
        if self.serial_connection:
            try:
                self.serial_connection.close()
            except:
                pass
            self.serial_connection = None
            
        self.connected = False
        self.status_var.set("Disconnected")
        self.status_label.config(foreground="red")
        self.connect_btn.config(text="Connect")
        
    def send_command(self, command):
        if self.connected and self.serial_connection:
            try:
                self.serial_connection.write((command + '\n').encode())
                if self.debug_mode_var.get():
                    print(f"Sent: {command}")
            except Exception as e:
                print(f"Error sending command: {e}")
                self.disconnect_from_arduino()
                
    # System Control Methods
    def toggle_system(self):
        enabled = 1 if self.system_enabled_var.get() else 0
        self.send_command(f"SYSTEM:{enabled}")
        
    def set_brightness(self, value):
        self.send_command(f"BRIGHTNESS:{value}")
        
    # Keyboard Methods
    def toggle_keyboard_monitoring(self):
        if self.keyboard_enabled_var.get():
            self.start_keyboard_monitoring()
        else:
            self.stop_keyboard_monitoring()
            
    def start_keyboard_monitoring(self):
        if not self.keyboard_listener:
            self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
            self.keyboard_listener.start()
            self.keyboard_enabled = True
            self.kb_status_var.set("Monitoring: Enabled")
            self.send_command("CONFIG:KB_ENABLE:1")
            
    def stop_keyboard_monitoring(self):
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
            self.keyboard_enabled = False
            self.kb_status_var.set("Monitoring: Disabled")
            self.send_command("CONFIG:KB_ENABLE:0")
            
    def on_key_press(self, key):
        if self.keyboard_enabled:
            current_time = time.time()
            self.last_key_time = current_time
            
            # Debounce keyboard triggers to prevent continuous animation
            if current_time - self.last_keyboard_trigger > self.keyboard_debounce_time:
                self.last_keyboard_trigger = current_time
                
                # Update UI
                try:
                    key_name = key.char if hasattr(key, 'char') and key.char else str(key)
                    self.last_key_var.set(f"Last Key: {key_name}")
                except:
                    self.last_key_var.set(f"Last Key: {str(key)}")
                    
                # Send to Arduino
                self.send_command("KEYBOARD:ON")
                
    def set_keyboard_mode(self):
        mode = self.keyboard_mode_var.get()
        self.send_command(f"CONFIG:KB_MODE:{mode}")
        
    def set_keyboard_duration(self, value):
        duration = int(float(value) * 1000)  # Convert to milliseconds
        self.send_command(f"CONFIG:KB_DURATION:{duration}")
        
    # Audio Methods
    def refresh_audio_devices(self):
        try:
            if not self.pyaudio_instance:
                print("PyAudio not initialized, attempting to initialize...")
                try:
                    self.pyaudio_instance = pyaudio.PyAudio()
                except Exception as e:
                    print(f"Failed to initialize PyAudio: {e}")
                    self.audio_device_combo['values'] = ["PyAudio not available"]
                    return
                
            devices = []
            device_count = self.pyaudio_instance.get_device_count()
            print(f"Found {device_count} audio devices")
            
            # First, add Stereo Mix if available (for system audio capture)
            stereo_mix_found = False
            for i in range(device_count):
                try:
                    info = self.pyaudio_instance.get_device_info_by_index(i)
                    if info['maxInputChannels'] > 0 and 'stereo mix' in info['name'].lower():
                        device_name = f"{i}: {info['name']} (System Audio)"
                        devices.append(device_name)
                        print(f"System audio device: {device_name}")
                        stereo_mix_found = True
                        break
                except Exception as e:
                    print(f"Error getting device {i}: {e}")
                    continue
            
            # Then add all other input devices
            for i in range(device_count):
                try:
                    info = self.pyaudio_instance.get_device_info_by_index(i)
                    if info['maxInputChannels'] > 0:
                        # Skip if it's already added as Stereo Mix
                        if not ('stereo mix' in info['name'].lower() and stereo_mix_found):
                            device_name = f"{i}: {info['name']}"
                            devices.append(device_name)
                            print(f"Input device: {device_name}")
                except Exception as e:
                    print(f"Error getting device {i}: {e}")
                    continue
            
            # Add a note about Stereo Mix if not found
            if not stereo_mix_found:
                devices.insert(0, "Note: Enable 'Stereo Mix' in Windows for system audio capture")
            
            self.audio_device_combo['values'] = devices
            if len(devices) > 1:  # More than just the note
                self.audio_device_combo.current(0)
                print(f"Loaded {len(devices)} audio devices")
            else:
                self.audio_device_combo['values'] = ["No input devices found"]
                print("No input devices found")
                
        except Exception as e:
            print(f"Error refreshing audio devices: {e}")
            import traceback
            traceback.print_exc()
            self.audio_device_combo['values'] = ["Error loading devices"]
            
    def toggle_audio_visualization(self):
        if self.audio_enabled_var.get():
            self.start_audio_monitoring()
        else:
            self.stop_audio_monitoring()
            
    def start_audio_monitoring(self):
        try:
            if not self.pyaudio_instance:
                messagebox.showerror("Audio Error", "PyAudio not available")
                self.audio_enabled_var.set(False)
                return
                
            selected_device = self.audio_device_var.get()
            if not selected_device or "No" in selected_device or "Error" in selected_device or "Note:" in selected_device:
                messagebox.showerror("Error", "Please select a valid audio device")
                self.audio_enabled_var.set(False)
                return
                
            device_index = int(selected_device.split(":")[0])
            
            # Try different sample rates for better compatibility
            sample_rates = [44100, 48000, 22050, 16000]
            audio_stream = None
            
            for rate in sample_rates:
                try:
                    audio_stream = self.pyaudio_instance.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=rate,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=1024
                    )
                    print(f"Audio stream opened successfully at {rate}Hz")
                    break
                except Exception as e:
                    print(f"Failed to open audio stream at {rate}Hz: {e}")
                    continue
            
            if not audio_stream:
                messagebox.showerror("Audio Error", "Failed to open audio stream with any sample rate")
                self.audio_enabled_var.set(False)
                return
            
            self.audio_stream = audio_stream
            self.audio_enabled = True
            self.audio_status_var.set("Audio: Enabled")
            self.send_command("CONFIG:AUDIO_ENABLE:1")
            
            # Show success message with device info
            device_name = selected_device.split(": ", 1)[1] if ": " in selected_device else selected_device
            messagebox.showinfo("Audio Enabled", f"Audio monitoring enabled on:\n{device_name}\n\nAdjust sensitivity if needed.")
            
        except Exception as e:
            messagebox.showerror("Audio Error", f"Failed to start audio monitoring: {str(e)}")
            self.audio_enabled_var.set(False)
            
    def stop_audio_monitoring(self):
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except:
                pass
            self.audio_stream = None
            
        self.audio_enabled = False
        self.audio_status_var.set("Audio: Disabled")
        self.send_command("CONFIG:AUDIO_ENABLE:0")
        
    def process_audio(self):
        if self.audio_enabled and self.audio_stream:
            try:
                data = self.audio_stream.read(1024, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                
                # Enhanced audio level calculation with better sensitivity
                # Use peak detection and RMS for better response
                peak_level = np.max(np.abs(audio_data))
                rms = np.sqrt(np.mean(audio_data**2))
                
                # Combine peak and RMS for better sensitivity
                combined_level = (peak_level * 0.3 + rms * 0.7)
                
                # Apply sensitivity with better scaling
                sensitivity = self.audio_sensitivity_var.get()
                audio_level = int(combined_level * sensitivity / 50)  # Increased sensitivity
                audio_level = min(255, max(0, audio_level))
                
                # Enhanced frequency analysis with better band separation
                fft = np.fft.fft(audio_data)
                freqs = np.abs(fft[:len(fft)//2])
                
                # Logarithmic frequency bands for better music response
                # Bass (20-150 Hz), Low Mid (150-400 Hz), Mid (400-800 Hz), 
                # High Mid (800-1600 Hz), High (1600-3200 Hz), Presence (3200-6400 Hz),
                # Brilliance (6400-12800 Hz), Air (12800-20000 Hz)
                sample_rate = 44100
                band_frequencies = [
                    (20, 150),    # Bass
                    (150, 400),   # Low Mid
                    (400, 800),   # Mid
                    (800, 1600),  # High Mid
                    (1600, 3200), # High
                    (3200, 6400), # Presence
                    (6400, 12800), # Brilliance
                    (12800, 20000) # Air
                ]
                
                bands = []
                for low_freq, high_freq in band_frequencies:
                    # Convert frequencies to FFT indices
                    low_idx = int(low_freq * len(freqs) / (sample_rate / 2))
                    high_idx = int(high_freq * len(freqs) / (sample_rate / 2))
                    
                    # Ensure valid indices
                    low_idx = max(0, min(low_idx, len(freqs) - 1))
                    high_idx = max(low_idx + 1, min(high_idx, len(freqs)))
                    
                    # Calculate band energy with peak detection
                    if high_idx > low_idx:
                        band_energy = np.mean(freqs[low_idx:high_idx])
                        band_peak = np.max(freqs[low_idx:high_idx])
                        # Combine average and peak for better response
                        band_level = (band_energy * 0.6 + band_peak * 0.4)
                    else:
                        band_level = 0
                    
                    # Apply sensitivity with better scaling
                    band_level = int(band_level * sensitivity / 200)  # Increased sensitivity
                    bands.append(min(255, max(0, band_level)))
                
                # Update UI with more detailed information
                self.audio_level_var.set(f"Level: {audio_level} (Peak: {peak_level}, RMS: {rms:.0f})")
                
                # Send to Arduino - match the format expected by Arduino
                bands_str = ",".join(map(str, bands))
                self.send_command(f"AUDIO:LEVEL:{audio_level},BANDS:{bands_str}")
                
            except Exception as e:
                if hasattr(self, 'debug_mode_var') and self.debug_mode_var.get():
                    print(f"Audio processing error: {e}")
                    
    def set_audio_mode(self):
        mode = self.audio_mode_var.get()
        self.send_command(f"CONFIG:AUDIO_MODE:{mode}")
        
    # Notification Methods
    def toggle_notifications(self):
        self.notification_enabled = self.notification_enabled_var.get()
        status = "Enabled" if self.notification_enabled else "Disabled"
        self.notif_status_var.set(f"Monitoring: {status}")
        
    def test_notification(self):
        self.send_command("NOTIFICATION:TEST")
        self.last_notif_var.set("Last Alert: Test Notification")
        
    def set_notification_mode(self):
        mode = self.notification_mode_var.get()
        self.send_command(f"CONFIG:NOTIF_MODE:{mode}")
        
    def monitor_notifications(self):
        # Simple notification monitoring using process names
        if not self.notification_enabled:
            return
            
        try:
            # Check for common notification-generating processes
            for proc in psutil.process_iter(['name']):
                proc_name = proc.info['name'].lower()
                
                # Check if any monitored apps are running
                for app_name, var in self.monitor_apps.items():
                    if var.get() and app_name.lower() in proc_name:
                        # This is a simplified check - in a real implementation,
                        # you'd want to use Windows notification APIs
                        pass
                        
        except Exception as e:
            if hasattr(self, 'debug_mode_var') and self.debug_mode_var.get():
                print(f"Notification monitoring error: {e}")
                
    # Idle Mode Methods
    def toggle_idle_mode(self):
        enabled = 1 if self.idle_enabled_var.get() else 0
        self.send_command(f"CONFIG:IDLE_ENABLE:{enabled}")
        status = "Enabled" if self.idle_enabled_var.get() else "Disabled"
        self.idle_status_var.set(f"Idle Mode: {status}")
        
    def set_idle_timeout(self, value):
        self.send_command(f"CONFIG:IDLE_TIMEOUT:{value}")
        
    def set_idle_mode(self):
        mode = self.idle_mode_var.get()
        self.send_command(f"CONFIG:IDLE_MODE:{mode}")
        
    # Settings Methods
    def load_settings(self):
        try:
            if os.path.exists('led_controller_settings.json'):
                with open('led_controller_settings.json', 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
        return {}
        
    def save_settings(self):
        settings = {
            'auto_connect': self.auto_connect_var.get(),
            'start_minimized': self.start_minimized_var.get(),
            'debug_mode': self.debug_mode_var.get(),
            'brightness': self.brightness_var.get(),
            'keyboard_mode': self.keyboard_mode_var.get(),
            'keyboard_duration': self.keyboard_duration_var.get(),
            'audio_mode': self.audio_mode_var.get(),
            'idle_mode': self.idle_mode_var.get(),
            'notification_mode': self.notification_mode_var.get(),
            'idle_timeout': self.idle_timeout_var.get(),
            'audio_sensitivity': self.audio_sensitivity_var.get()
        }
        
        try:
            with open('led_controller_settings.json', 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
            
    def save_profile(self):
        # Save current settings as a profile
        self.save_settings()
        messagebox.showinfo("Profile Saved", "Current settings saved as default profile")
        
    def load_profile(self):
        # Load settings from file
        self.settings = self.load_settings()
        self.apply_loaded_settings()
        messagebox.showinfo("Profile Loaded", "Settings loaded from saved profile")
        
    def apply_loaded_settings(self):
        # Apply loaded settings to UI
        if 'brightness' in self.settings:
            self.brightness_var.set(self.settings['brightness'])
        if 'keyboard_mode' in self.settings:
            self.keyboard_mode_var.set(self.settings['keyboard_mode'])
        if 'keyboard_duration' in self.settings:
            self.keyboard_duration_var.set(self.settings['keyboard_duration'])
        if 'audio_mode' in self.settings:
            self.audio_mode_var.set(self.settings['audio_mode'])
        if 'idle_mode' in self.settings:
            self.idle_mode_var.set(self.settings['idle_mode'])
        if 'notification_mode' in self.settings:
            self.notification_mode_var.set(self.settings['notification_mode'])
        if 'idle_timeout' in self.settings:
            self.idle_timeout_var.set(self.settings['idle_timeout'])
        if 'audio_sensitivity' in self.settings:
            self.audio_sensitivity_var.set(self.settings['audio_sensitivity'])
            
    def reset_settings(self):
        # Reset all settings to defaults
        self.brightness_var.set(200)
        self.keyboard_mode_var.set(0)
        self.keyboard_duration_var.set(1)
        self.audio_mode_var.set(0)
        self.idle_mode_var.set(0)
        self.notification_mode_var.set(1)
        self.idle_timeout_var.set(30)
        self.audio_sensitivity_var.set(50)
        
        self.send_all_settings()
        messagebox.showinfo("Settings Reset", "All settings reset to defaults")
        
    def send_all_settings(self):
        # Send all current settings to Arduino
        self.toggle_system()
        self.set_brightness(self.brightness_var.get())
        self.set_keyboard_mode()
        self.set_keyboard_duration(self.keyboard_duration_var.get())
        self.set_audio_mode()
        self.set_idle_mode()
        self.set_notification_mode()
        self.set_idle_timeout(self.idle_timeout_var.get())
        
    # Background Thread Methods
    def start_background_threads(self):
        # Audio processing thread
        self.audio_thread = threading.Thread(target=self.audio_worker, daemon=True)
        self.audio_thread.start()
        
        # Notification monitoring thread
        self.notification_thread = threading.Thread(target=self.notification_worker, daemon=True)
        self.notification_thread.start()
        
    def audio_worker(self):
        while self.running:
            try:
                self.process_audio()
                time.sleep(0.05)  # 20 FPS
            except Exception as e:
                if hasattr(self, 'debug_mode_var') and self.debug_mode_var.get():
                    print(f"Audio worker error: {e}")
                time.sleep(1)
                
    def notification_worker(self):
        while self.running:
            try:
                self.monitor_notifications()
                time.sleep(1)  # Check every second
            except Exception as e:
                if hasattr(self, 'debug_mode_var') and self.debug_mode_var.get():
                    print(f"Notification worker error: {e}")
                time.sleep(5)
                
    def on_closing(self):
        self.running = False
        
        # Stop all monitoring
        self.stop_keyboard_monitoring()
        self.stop_audio_monitoring()
        
        # Disconnect from Arduino
        self.disconnect_from_arduino()
        
        # Clean up PyAudio
        if self.pyaudio_instance:
            try:
                self.pyaudio_instance.terminate()
            except:
                pass
        
        # Save settings
        self.save_settings()
        
        # Close application
        self.root.destroy()
        
    def run(self):
        # Auto-connect if enabled
        if self.settings.get('auto_connect', False):
            self.root.after(1000, self.connect_to_arduino)
            
        # Start minimized if enabled
        if self.settings.get('start_minimized', False):
            self.root.withdraw()
            
        self.root.mainloop()

    def test_audio_level(self):
        """Test audio level without starting full monitoring"""
        try:
            if not self.pyaudio_instance:
                messagebox.showerror("Error", "PyAudio not available")
                return
                
            selected_device = self.audio_device_var.get()
            if not selected_device or "No" in selected_device or "Error" in selected_device or "Note:" in selected_device:
                messagebox.showerror("Error", "Please select a valid audio device first")
                return
                
            device_index = int(selected_device.split(":")[0])
            
            # Open temporary audio stream for testing
            test_stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=1024
            )
            
            # Test for 3 seconds
            import threading
            import time
            
            def test_audio():
                max_level = 0
                samples = 0
                
                for _ in range(30):  # 3 seconds at 10 samples per second
                    try:
                        data = test_stream.read(1024, exception_on_overflow=False)
                        audio_data = np.frombuffer(data, dtype=np.int16)
                        
                        peak_level = np.max(np.abs(audio_data))
                        rms = np.sqrt(np.mean(audio_data**2))
                        combined_level = (peak_level * 0.3 + rms * 0.7)
                        
                        sensitivity = self.audio_sensitivity_var.get()
                        audio_level = int(combined_level * sensitivity / 50)
                        audio_level = min(255, max(0, audio_level))
                        
                        max_level = max(max_level, audio_level)
                        samples += 1
                        
                        # Update UI
                        self.audio_level_var.set(f"Testing... Level: {audio_level}")
                        time.sleep(0.1)
                        
                    except Exception as e:
                        print(f"Test error: {e}")
                        break
                
                # Close test stream
                test_stream.stop_stream()
                test_stream.close()
                
                # Show results
                if samples > 0:
                    if max_level > 10:
                        messagebox.showinfo("Audio Test Results", 
                                          f"Audio detected successfully!\n"
                                          f"Maximum level: {max_level}/255\n"
                                          f"Device is working properly.\n\n"
                                          f"Try increasing sensitivity if levels are low.")
                    else:
                        messagebox.showwarning("Audio Test Results", 
                                             f"Very low audio levels detected.\n"
                                             f"Maximum level: {max_level}/255\n\n"
                                             f"Suggestions:\n"
                                             f"• Increase system volume\n"
                                             f"• Increase audio sensitivity\n"
                                             f"• Check if audio is playing\n"
                                             f"• Try a different audio device")
                else:
                    messagebox.showerror("Audio Test Results", 
                                       "No audio detected.\n"
                                       "Check your audio device and settings.")
                
                # Reset status
                self.audio_level_var.set("Level: 0")
            
            # Run test in background thread
            test_thread = threading.Thread(target=test_audio, daemon=True)
            test_thread.start()
            
        except Exception as e:
            messagebox.showerror("Test Error", f"Failed to test audio: {str(e)}")

if __name__ == "__main__":
    # Install required packages if not present
    required_packages = ['pyaudio', 'numpy', 'pynput', 'pyserial', 'psutil', 'win10toast']
    
    try:
        import pyaudio
        import numpy as np
        from pynput import keyboard
        import serial
        import psutil
        import win10toast
    except ImportError as e:
        print(f"Missing required package: {e}")
        print("Please install required packages:")
        print("pip install pyaudio numpy pynput pyserial psutil win10toast")
        sys.exit(1)
    
    app = LEDController()
    app.run()