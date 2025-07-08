import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import serial
import serial.tools.list_ports
import time
import threading
from pynput import keyboard
import numpy as np
import sounddevice as sd
from scipy.fft import fft
import colorsys
import psutil
import win32gui
import win32con
import win32api
import win32process
from winotify import Notification, audio
import json
import os

class LEDControllerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Professional LED Controller v3")
        self.root.geometry("1000x800")
        self.root.configure(bg='#2b2b2b')
        
        # Variables
        self.arduino = None
        self.is_monitoring = False
        self.keyboard_listener = None
        self.monitor_thread = None
        self.last_key_time = 0
        self.current_mode = "Disconnected"
        self.audio_monitoring = False
        self.audio_thread = None
        self.notification_monitoring = False
        self.notification_thread = None
        
        # Custom effect variables
        self.custom_color = "#FF0000"
        self.custom_speed = 50
        self.custom_brightness = 100
        
        # Key reactive effect variables
        self.selected_key_effects = ["ripple", "explosion", "wave", "sparkle"]
        self.key_effect_intensity = 50
        
        # Audio variables
        self.audio_sensitivity = 10
        self.audio_spectrum_bands = 8
        self.system_audio_device = None
        
        # Notification variables
        self.notification_sensitivity = 5
        self.last_notification_time = 0
        self.notification_cooldown = 2.0  # seconds
        
        self.setup_ui()
        self.refresh_ports()
        self.detect_audio_devices()
        
    def setup_ui(self):
        # Main frame with scrollbar
        main_canvas = tk.Canvas(self.root, bg='#2b2b2b')
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas, bg='#2b2b2b')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Connection Frame
        conn_frame = tk.LabelFrame(scrollable_frame, text="Connection", bg='#2b2b2b', fg='white', font=('Arial', 12, 'bold'))
        conn_frame.pack(fill=tk.X, pady=(10, 10), padx=10)
        
        # Port selection
        tk.Label(conn_frame, text="Select Port:", bg='#2b2b2b', fg='white').grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var, width=30, state='readonly')
        self.port_combo.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(conn_frame, text="Refresh", command=self.refresh_ports, bg='#4CAF50', fg='white').grid(row=0, column=2, padx=5, pady=5)
        tk.Button(conn_frame, text="Connect", command=self.connect_arduino, bg='#2196F3', fg='white').grid(row=0, column=3, padx=5, pady=5)
        tk.Button(conn_frame, text="Disconnect", command=self.disconnect_arduino, bg='#f44336', fg='white').grid(row=0, column=4, padx=5, pady=5)
        
        # Status
        self.status_label = tk.Label(conn_frame, text="Status: Disconnected", bg='#2b2b2b', fg='red', font=('Arial', 10, 'bold'))
        self.status_label.grid(row=1, column=0, columnspan=5, pady=5)
        
        # Mode Selection Frame
        mode_frame = tk.LabelFrame(scrollable_frame, text="Mode Selection", bg='#2b2b2b', fg='white', font=('Arial', 12, 'bold'))
        mode_frame.pack(fill=tk.X, pady=(0, 10), padx=10)
        
        # Mode buttons
        modes = [
            ("Key Reactive + Notification + Idle", "full"),
            ("Key Reactive + Idle", "key_idle"),
            ("Key Reactive Only", "key_only"),
            ("Idle Only", "idle_only"),
            ("Key Reactive + Notification", "key_notify"),
            ("Notification Only", "notify_only"),
            ("Custom Effects", "custom")
        ]
        
        for i, (text, mode) in enumerate(modes):
            row = i // 2
            col = i % 2
            btn = tk.Button(mode_frame, text=text, command=lambda m=mode: self.set_mode(m), 
                          bg='#3f3f3f', fg='white', width=25, height=2)
            btn.grid(row=row, column=col, padx=5, pady=5)
        
        # Key Reactive Effects Frame
        key_frame = tk.LabelFrame(scrollable_frame, text="Key Reactive Effects", bg='#2b2b2b', fg='white', font=('Arial', 12, 'bold'))
        key_frame.pack(fill=tk.X, pady=(0, 10), padx=10)
        
        # Key effect selection
        key_effects = [
            ("Ripple", "ripple"),
            ("Explosion", "explosion"),
            ("Wave", "wave"),
            ("Sparkle", "sparkle"),
            ("Pulse", "pulse"),
            ("Comet", "comet"),
            ("Firework", "firework"),
            ("Lightning", "lightning")
        ]
        
        self.key_effect_vars = {}
        for i, (text, effect) in enumerate(key_effects):
            row = i // 4
            col = i % 4
            var = tk.BooleanVar(value=effect in self.selected_key_effects)
            self.key_effect_vars[effect] = var
            cb = tk.Checkbutton(key_frame, text=text, variable=var, bg='#2b2b2b', fg='white', selectcolor='#4CAF50')
            cb.grid(row=row, column=col, padx=5, pady=5, sticky='w')
        
        # Key effect intensity
        tk.Label(key_frame, text="Effect Intensity:", bg='#2b2b2b', fg='white').grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.key_intensity_scale = tk.Scale(key_frame, from_=1, to=100, orient=tk.HORIZONTAL, bg='#2b2b2b', fg='white')
        self.key_intensity_scale.set(self.key_effect_intensity)
        self.key_intensity_scale.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky='ew')
        
        # Custom Effects Frame
        self.custom_frame = tk.LabelFrame(scrollable_frame, text="Custom Effects", bg='#2b2b2b', fg='white', font=('Arial', 12, 'bold'))
        self.custom_frame.pack(fill=tk.X, pady=(0, 10), padx=10)
        
        # Custom effects buttons
        custom_effects = [
            ("Solid Color", "solid"),
            ("Sand Clock", "sandclock"),
            ("Rainbow", "rainbow"),
            ("Audio Reactive", "audio"),
            ("Breathing", "breathing"),
            ("Color Wipe", "colorwipe"),
            ("Sparkle", "sparkle"),
            ("Fire Effect", "fire"),
            ("Spectrum", "spectrum"),
            ("Wave", "wave"),
            ("Matrix", "matrix")
        ]
        
        for i, (text, effect) in enumerate(custom_effects):
            row = i // 4
            col = i % 4
            btn = tk.Button(self.custom_frame, text=text, command=lambda e=effect: self.custom_effect(e),
                          bg='#6a4c93', fg='white', width=15)
            btn.grid(row=row, column=col, padx=5, pady=5)
        
        # Custom Settings Frame
        settings_frame = tk.LabelFrame(scrollable_frame, text="Custom Settings", bg='#2b2b2b', fg='white', font=('Arial', 12, 'bold'))
        settings_frame.pack(fill=tk.X, pady=(0, 10), padx=10)
        
        # Color picker
        tk.Label(settings_frame, text="Color:", bg='#2b2b2b', fg='white').grid(row=0, column=0, padx=5, pady=5)
        self.color_button = tk.Button(settings_frame, text="  ", bg=self.custom_color, width=5, command=self.choose_color)
        self.color_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Speed control
        tk.Label(settings_frame, text="Speed:", bg='#2b2b2b', fg='white').grid(row=0, column=2, padx=5, pady=5)
        self.speed_scale = tk.Scale(settings_frame, from_=1, to=100, orient=tk.HORIZONTAL, bg='#2b2b2b', fg='white')
        self.speed_scale.set(self.custom_speed)
        self.speed_scale.grid(row=0, column=3, padx=5, pady=5)
        
        # Brightness control
        tk.Label(settings_frame, text="Brightness:", bg='#2b2b2b', fg='white').grid(row=0, column=4, padx=5, pady=5)
        self.brightness_scale = tk.Scale(settings_frame, from_=10, to=255, orient=tk.HORIZONTAL, bg='#2b2b2b', fg='white')
        self.brightness_scale.set(self.custom_brightness)
        self.brightness_scale.grid(row=0, column=5, padx=5, pady=5)
        
        # Audio Settings Frame
        audio_frame = tk.LabelFrame(scrollable_frame, text="Audio Settings", bg='#2b2b2b', fg='white', font=('Arial', 12, 'bold'))
        audio_frame.pack(fill=tk.X, pady=(0, 10), padx=10)
        
        # Audio device selection
        tk.Label(audio_frame, text="Audio Device:", bg='#2b2b2b', fg='white').grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.audio_device_var = tk.StringVar()
        self.audio_device_combo = ttk.Combobox(audio_frame, textvariable=self.audio_device_var, width=40, state='readonly')
        self.audio_device_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Audio sensitivity control
        tk.Label(audio_frame, text="Audio Sensitivity:", bg='#2b2b2b', fg='white').grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.audio_sensitivity_scale = tk.Scale(audio_frame, from_=1, to=50, orient=tk.HORIZONTAL, bg='#2b2b2b', fg='white')
        self.audio_sensitivity_scale.set(self.audio_sensitivity)
        self.audio_sensitivity_scale.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        
        # Notification Settings Frame
        notify_frame = tk.LabelFrame(scrollable_frame, text="Notification Settings", bg='#2b2b2b', fg='white', font=('Arial', 12, 'bold'))
        notify_frame.pack(fill=tk.X, pady=(0, 10), padx=10)
        
        # Notification sensitivity
        tk.Label(notify_frame, text="Notification Sensitivity:", bg='#2b2b2b', fg='white').grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.notify_sensitivity_scale = tk.Scale(notify_frame, from_=1, to=20, orient=tk.HORIZONTAL, bg='#2b2b2b', fg='white')
        self.notify_sensitivity_scale.set(self.notification_sensitivity)
        self.notify_sensitivity_scale.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        
        # Notification cooldown
        tk.Label(notify_frame, text="Cooldown (seconds):", bg='#2b2b2b', fg='white').grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.notify_cooldown_scale = tk.Scale(notify_frame, from_=0.5, to=10.0, resolution=0.5, orient=tk.HORIZONTAL, bg='#2b2b2b', fg='white')
        self.notify_cooldown_scale.set(self.notification_cooldown)
        self.notify_cooldown_scale.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        
        # Control Frame
        control_frame = tk.LabelFrame(scrollable_frame, text="Controls", bg='#2b2b2b', fg='white', font=('Arial', 12, 'bold'))
        control_frame.pack(fill=tk.X, pady=(0, 10), padx=10)
        
        tk.Button(control_frame, text="Test Notification", command=self.test_notification, bg='#ff9800', fg='white').pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(control_frame, text="Test Key Press", command=self.test_key_press, bg='#9c27b0', fg='white').pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(control_frame, text="Turn Off LEDs", command=self.turn_off_leds, bg='#f44336', fg='white').pack(side=tk.LEFT, padx=5, pady=5)
        
        # Status indicators
        status_frame = tk.Frame(control_frame, bg='#2b2b2b')
        status_frame.pack(side=tk.RIGHT, padx=10, pady=5)
        
        self.audio_status = tk.Label(status_frame, text="Audio: OFF", bg='#2b2b2b', fg='red', font=('Arial', 10, 'bold'))
        self.audio_status.pack(side=tk.TOP, pady=2)
        
        self.notify_status = tk.Label(status_frame, text="Notifications: OFF", bg='#2b2b2b', fg='red', font=('Arial', 10, 'bold'))
        self.notify_status.pack(side=tk.TOP, pady=2)
        
        # Log Frame
        log_frame = tk.LabelFrame(scrollable_frame, text="Activity Log", bg='#2b2b2b', fg='white', font=('Arial', 12, 'bold'))
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=10)
        
        self.log_text = tk.Text(log_frame, height=10, bg='#1e1e1e', fg='#00ff00', font=('Consolas', 9))
        scrollbar = tk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)
        
        self.log("LED Controller GUI v3 Started")
        
    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = []
        for port in ports:
            port_list.append(f"{port.device} - {port.description}")
        
        self.port_combo['values'] = port_list
        if port_list:
            self.port_combo.current(0)
            self.log(f"Found {len(port_list)} serial ports")
        else:
            self.log("No serial ports found")
            
    def detect_audio_devices(self):
        """Detect available audio devices for system audio capture"""
        try:
            devices = sd.query_devices()
            device_list = []
            
            for i, device in enumerate(devices):
                if device['max_inputs'] > 0:  # Input device
                    device_list.append(f"{i}: {device['name']}")
            
            self.audio_device_combo['values'] = device_list
            if device_list:
                self.audio_device_combo.current(0)
                self.log(f"Found {len(device_list)} audio input devices")
            else:
                self.log("No audio input devices found")
                
        except Exception as e:
            self.log(f"Error detecting audio devices: {e}")
            
    def connect_arduino(self):
        if not self.port_var.get():
            messagebox.showerror("Error", "Please select a port")
            return
            
        port_name = self.port_var.get().split(' - ')[0]
        
        try:
            self.arduino = serial.Serial(port_name, 9600, timeout=1)
            time.sleep(2)  # Wait for Arduino to initialize
            self.status_label.config(text=f"Status: Connected to {port_name}", fg='green')
            self.log(f"Connected to Arduino on {port_name}")
            
            # Send initial command to test connection
            self.send_command("IDLE")
            
        except serial.SerialException as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
            self.log(f"Connection failed: {e}")
            
    def disconnect_arduino(self):
        if self.arduino:
            self.stop_monitoring()
            self.stop_audio_monitoring()
            self.stop_notification_monitoring()
            self.arduino.close()
            self.arduino = None
            self.status_label.config(text="Status: Disconnected", fg='red')
            self.log("Disconnected from Arduino")
            
    def send_command(self, command):
        if self.arduino:
            try:
                self.arduino.write(f"{command}\n".encode())
                self.log(f"Sent: {command}")
            except Exception as e:
                self.log(f"Error sending command: {e}")
        else:
            self.log("Arduino not connected")
            
    def set_mode(self, mode):
        if not self.arduino:
            messagebox.showerror("Error", "Please connect to Arduino first")
            return
            
        self.stop_monitoring()
        self.stop_audio_monitoring()
        self.stop_notification_monitoring()
        self.current_mode = mode
        
        mode_names = {
            "full": "Key Reactive + Notification + Idle",
            "key_idle": "Key Reactive + Idle",
            "key_only": "Key Reactive Only",
            "idle_only": "Idle Only",
            "key_notify": "Key Reactive + Notification",
            "notify_only": "Notification Only",
            "custom": "Custom Effects"
        }
        
        self.log(f"Mode set to: {mode_names.get(mode, mode)}")
        
        if mode == "custom":
            self.log("Custom mode active. Select an effect from Custom Effects section.")
        else:
            self.start_monitoring(mode)
            
    def start_monitoring(self, mode):
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, args=(mode,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # Start keyboard listener if needed
        if "key" in mode or mode == "full":
            self.start_keyboard_listener()
            
        # Start notification monitoring if needed
        if "notify" in mode or mode == "full":
            self.start_notification_monitoring()
            
        self.log("Monitoring started")
        
    def stop_monitoring(self):
        self.is_monitoring = False
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
            
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
            
        self.log("Monitoring stopped")
        
    def stop_audio_monitoring(self):
        """Stop audio monitoring thread and update status"""
        self.audio_monitoring = False
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=1)
            self.audio_thread = None
        self.audio_status.config(text="Audio: OFF", fg='red')
        self.log("Audio monitoring stopped")
        
    def stop_notification_monitoring(self):
        """Stop notification monitoring thread and update status"""
        self.notification_monitoring = False
        if self.notification_thread and self.notification_thread.is_alive():
            self.notification_thread.join(timeout=1)
            self.notification_thread = None
        self.notify_status.config(text="Notifications: OFF", fg='red')
        self.log("Notification monitoring stopped")
        
    def start_keyboard_listener(self):
        def on_key_press(key):
            if self.is_monitoring:
                self.last_key_time = time.time()
                try:
                    key_name = key.char if hasattr(key, 'char') and key.char else str(key)
                    self.log(f"Key pressed: {key_name}")
                except AttributeError:
                    self.log(f"Special key pressed: {key}")
                
                # Send key effect command with random effect type
                self.send_random_key_effect()
        
        try:
            self.keyboard_listener = keyboard.Listener(on_press=on_key_press)
            self.keyboard_listener.start()
        except Exception as e:
            self.log(f"Keyboard listener error: {e}")
            
    def send_random_key_effect(self):
        """Send a random key effect command"""
        # Get selected effects
        selected_effects = [effect for effect, var in self.key_effect_vars.items() if var.get()]
        
        if not selected_effects:
            selected_effects = ["ripple"]  # Default effect
            
        # Choose random effect
        effect_type = selected_effects[int(time.time() * 1000) % len(selected_effects)]
        position = int(time.time() * 1000) % 60  # Random position
        
        command = f"KEYEFFECT,{effect_type},{position}"
        self.send_command(command)
        
    def start_notification_monitoring(self):
        """Start monitoring for system notifications"""
        if self.notification_monitoring:
            return
            
        self.notification_monitoring = True
        self.notification_thread = threading.Thread(target=self.notification_monitor_loop)
        self.notification_thread.daemon = True
        self.notification_thread.start()
        
        self.notify_status.config(text="Notifications: ON", fg='green')
        self.log("Notification monitoring started")
        
    def notification_monitor_loop(self):
        """Monitor for system notifications"""
        try:
            # Get initial window list
            initial_windows = self.get_active_windows()
            
            while self.notification_monitoring:
                time.sleep(0.5)  # Check every 500ms
                
                current_windows = self.get_active_windows()
                
                # Check for new notification windows
                for window in current_windows:
                    if window not in initial_windows and self.is_notification_window(window):
                        if time.time() - self.last_notification_time > self.notification_cooldown:
                            self.send_command("NOTIFY")
                            self.last_notification_time = time.time()
                            self.log(f"Notification detected: {window}")
                            break
                
                initial_windows = current_windows
                
        except Exception as e:
            self.log(f"Notification monitoring error: {e}")
            self.notify_status.config(text="Notifications: ERROR", fg='orange')
            
    def get_active_windows(self):
        """Get list of currently active windows"""
        windows = []
        
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                if window_text and len(window_text) > 0:
                    windows.append(window_text)
            return True
        
        win32gui.EnumWindows(enum_windows_callback, windows)
        return windows
        
    def is_notification_window(self, window_title):
        """Check if a window is likely a notification"""
        notification_keywords = [
            "notification", "alert", "message", "mail", "email", "chat", "message",
            "whatsapp", "telegram", "discord", "slack", "teams", "outlook", "gmail",
            "facebook", "twitter", "instagram", "youtube", "twitch", "steam"
        ]
        
        window_lower = window_title.lower()
        
        # Check for notification keywords
        for keyword in notification_keywords:
            if keyword in window_lower:
                return True
                
        # Check for common notification patterns
        if any(pattern in window_lower for pattern in ["new message", "unread", "mention", "reply"]):
            return True
            
        return False
        
    def monitor_loop(self, mode):
        notification_counter = 0
        
        # Initialize based on mode
        if "idle" in mode or mode == "full":
            self.send_command("IDLE")
            
        while self.is_monitoring:
            current_time = time.time()
            
            # Handle idle timeout
            if ("key" in mode or mode == "full") and current_time - self.last_key_time > 5:
                if "idle" in mode or mode == "full":
                    self.send_command("IDLE")
                    
            time.sleep(0.1)
            
    def custom_effect(self, effect):
        if not self.arduino:
            messagebox.showerror("Error", "Please connect to Arduino first")
            return
            
        self.stop_monitoring()
        self.stop_audio_monitoring()
        
        # Get current settings
        color = self.custom_color
        speed = self.speed_scale.get()
        brightness = self.brightness_scale.get()
        
        # Convert color to RGB
        color = color.lstrip('#')
        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        
        command = f"CUSTOM,{effect},{r},{g},{b},{speed},{brightness}"
        self.send_command(command)
        
        self.log(f"Custom effect: {effect} (R:{r}, G:{g}, B:{b}, Speed:{speed}, Brightness:{brightness})")
        
        # Start audio monitoring if audio reactive
        if effect in ["audio", "spectrum"]:
            self.start_audio_monitoring()
            
    def start_audio_monitoring(self):
        """Start audio monitoring in a separate thread"""
        if self.audio_monitoring:
            return
            
        self.audio_monitoring = True
        self.audio_thread = threading.Thread(target=self.audio_monitor_loop)
        self.audio_thread.daemon = True
        self.audio_thread.start()
        
        self.audio_status.config(text="Audio: ON", fg='green')
        self.log("Audio monitoring started")
        
    def audio_monitor_loop(self):
        """Main audio monitoring loop using system audio"""
        try:
            # Get selected audio device
            device_str = self.audio_device_var.get()
            if not device_str:
                self.log("No audio device selected")
                return
                
            device_id = int(device_str.split(':')[0])
            
            # Audio parameters
            sample_rate = 44100
            block_size = 1024
            
            def audio_callback(indata, frames, time, status):
                if not self.audio_monitoring:
                    return
                    
                try:
                    # Get audio data from first channel
                    audio_data = indata[:, 0] if indata.shape[1] > 1 else indata.flatten()
                    
                    # Calculate FFT for spectrum analysis
                    fft_data = np.abs(fft(audio_data))
                    fft_data = fft_data[:len(fft_data)//2]  # Take only positive frequencies
                    
                    # Divide into 8 frequency bands
                    bands = []
                    band_size = len(fft_data) // 8
                    for i in range(8):
                        start = i * band_size
                        end = start + band_size
                        band_energy = np.mean(fft_data[start:end])
                        bands.append(int(np.clip(band_energy * 100, 0, 255)))
                    
                    # Calculate RMS for overall volume
                    rms = np.sqrt(np.mean(audio_data**2))
                    
                    # Apply sensitivity scaling
                    sensitivity = self.audio_sensitivity_scale.get()
                    volume = rms * sensitivity * 1000
                    
                    # Clamp to valid range
                    overall_level = int(np.clip(volume, 0, 255))
                    
                    # Send spectrum data
                    spectrum_command = f"AUDIO,{','.join(map(str, bands))}"
                    self.send_command(spectrum_command)
                    
                    # Only send if above threshold to reduce noise
                    if overall_level > 15:
                        self.send_command(f"AUDIO,{overall_level}")
                        
                except Exception as e:
                    self.log(f"Audio callback error: {e}")
            
            # Start audio stream
            with sd.InputStream(
                device=device_id,
                callback=audio_callback,
                channels=1,
                samplerate=sample_rate,
                blocksize=block_size,
                dtype=np.float32
            ):
                self.log(f"Audio stream started (Device: {device_id}, SR: {sample_rate}, Block: {block_size})")
                
                while self.audio_monitoring:
                    time.sleep(0.1)
                    
        except Exception as e:
            self.log(f"Audio monitoring error: {e}")
            self.audio_status.config(text="Audio: ERROR", fg='orange')
        finally:
            self.audio_monitoring = False
            self.audio_status.config(text="Audio: OFF", fg='red')
            
    def choose_color(self):
        color = colorchooser.askcolor(title="Choose LED Color")[1]
        if color:
            self.custom_color = color
            self.color_button.config(bg=color)
            
    def test_notification(self):
        self.send_command("NOTIFY")
        self.log("Test notification sent")
        
    def test_key_press(self):
        self.send_random_key_effect()
        self.log("Test key effect sent")
        
    def turn_off_leds(self):
        self.send_command("OFF")
        self.stop_audio_monitoring()
        self.log("LEDs turned off")
        
    def on_closing(self):
        self.stop_monitoring()
        self.stop_audio_monitoring()
        self.stop_notification_monitoring()
        if self.arduino:
            self.arduino.close()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = LEDControllerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main() 