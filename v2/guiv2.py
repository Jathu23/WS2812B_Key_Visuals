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

class LEDControllerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Professional LED Controller")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
        
        # Variables
        self.arduino = None
        self.is_monitoring = False
        self.keyboard_listener = None
        self.monitor_thread = None
        self.last_key_time = 0
        self.current_mode = "Disconnected"
        self.audio_monitoring = False
        self.audio_thread = None  # Add audio thread variable
        
        # Custom effect variables
        self.custom_color = "#FF0000"
        self.custom_speed = 50
        self.custom_brightness = 100
        
        self.setup_ui()
        self.refresh_ports()
        
    def setup_ui(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Connection Frame
        conn_frame = tk.LabelFrame(main_frame, text="Connection", bg='#2b2b2b', fg='white', font=('Arial', 12, 'bold'))
        conn_frame.pack(fill=tk.X, pady=(0, 10))
        
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
        mode_frame = tk.LabelFrame(main_frame, text="Mode Selection", bg='#2b2b2b', fg='white', font=('Arial', 12, 'bold'))
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
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
        
        # Key Reactive Style Dropdown
        key_styles = ["Center Ripple", "Pulse", "Color Burst"]
        self.key_style_var = tk.StringVar(value=key_styles[0])
        tk.Label(mode_frame, text="Key Reactive Style:", bg='#2b2b2b', fg='white').grid(row=4, column=0, padx=5, pady=5, sticky='e')
        self.key_style_combo = ttk.Combobox(mode_frame, textvariable=self.key_style_var, values=key_styles, state='readonly', width=20)
        self.key_style_combo.grid(row=4, column=1, padx=5, pady=5, sticky='w')
        
        # Custom Effects Frame
        self.custom_frame = tk.LabelFrame(main_frame, text="Custom Effects", bg='#2b2b2b', fg='white', font=('Arial', 12, 'bold'))
        self.custom_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Custom effects buttons
        custom_effects = [
            ("Solid Color", "solid"),
            ("Sand Clock", "sandclock"),
            ("Rainbow", "rainbow"),
            ("Audio Reactive", "audio"),
            ("Breathing", "breathing"),
            ("Color Wipe", "colorwipe"),
            ("Sparkle", "sparkle"),
            ("Fire Effect", "fire")
        ]
        
        for i, (text, effect) in enumerate(custom_effects):
            row = i // 4
            col = i % 4
            btn = tk.Button(self.custom_frame, text=text, command=lambda e=effect: self.custom_effect(e),
                          bg='#6a4c93', fg='white', width=15)
            btn.grid(row=row, column=col, padx=5, pady=5)
        
        # Custom Settings Frame
        settings_frame = tk.LabelFrame(main_frame, text="Custom Settings", bg='#2b2b2b', fg='white', font=('Arial', 12, 'bold'))
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
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
        
        # Audio sensitivity control (new)
        tk.Label(settings_frame, text="Audio Sensitivity:", bg='#2b2b2b', fg='white').grid(row=1, column=0, padx=5, pady=5)
        self.audio_sensitivity = tk.Scale(settings_frame, from_=1, to=50, orient=tk.HORIZONTAL, bg='#2b2b2b', fg='white')
        self.audio_sensitivity.set(10)
        self.audio_sensitivity.grid(row=1, column=1, padx=5, pady=5)
        
        # Audio Effect Style Dropdown
        audio_styles = ["Bar", "Spectrum", "Color Wave"]
        self.audio_style_var = tk.StringVar(value=audio_styles[0])
        tk.Label(settings_frame, text="Audio Effect Style:", bg='#2b2b2b', fg='white').grid(row=1, column=2, padx=5, pady=5, sticky='e')
        self.audio_style_combo = ttk.Combobox(settings_frame, textvariable=self.audio_style_var, values=audio_styles, state='readonly', width=15)
        self.audio_style_combo.grid(row=1, column=3, padx=5, pady=5, sticky='w')
        
        # Control Frame
        control_frame = tk.LabelFrame(main_frame, text="Controls", bg='#2b2b2b', fg='white', font=('Arial', 12, 'bold'))
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Button(control_frame, text="Test Notification", command=self.test_notification, bg='#ff9800', fg='white').pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(control_frame, text="Test Key Press", command=self.test_key_press, bg='#9c27b0', fg='white').pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(control_frame, text="Turn Off LEDs", command=self.turn_off_leds, bg='#f44336', fg='white').pack(side=tk.LEFT, padx=5, pady=5)
        
        # Audio status indicator (new)
        self.audio_status = tk.Label(control_frame, text="Audio: OFF", bg='#2b2b2b', fg='red', font=('Arial', 10, 'bold'))
        self.audio_status.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Log Frame
        log_frame = tk.LabelFrame(main_frame, text="Activity Log", bg='#2b2b2b', fg='white', font=('Arial', 12, 'bold'))
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, height=10, bg='#1e1e1e', fg='#00ff00', font=('Consolas', 9))
        scrollbar = tk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)
        
        self.log("LED Controller GUI Started")
        
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
            self.stop_audio_monitoring()  # Stop audio monitoring
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
        self.stop_audio_monitoring()  # Stop audio monitoring when changing modes
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
        
    def start_keyboard_listener(self):
        def on_key_press(key):
            if self.is_monitoring:
                self.last_key_time = time.time()
                try:
                    key_name = key.char if hasattr(key, 'char') and key.char else str(key)
                    self.log(f"Key pressed: {key_name}")
                except AttributeError:
                    self.log(f"Special key pressed: {key}")
                # Send key command with selected style
                style = self.key_style_var.get().replace(" ", "_").lower()
                self.send_command(f"KEY,{style}")
        
        try:
            self.keyboard_listener = keyboard.Listener(on_press=on_key_press)
            self.keyboard_listener.start()
        except Exception as e:
            self.log(f"Keyboard listener error: {e}")
            
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
                    
            # Handle notifications
            if "notify" in mode or mode == "full":
                notification_counter += 1
                if notification_counter >= 300:  # Every 30 seconds (100ms * 300)
                    self.send_command("NOTIFY")
                    notification_counter = 0
                    
            time.sleep(0.1)
            
    def custom_effect(self, effect):
        if not self.arduino:
            messagebox.showerror("Error", "Please connect to Arduino first")
            return
            
        self.stop_monitoring()
        self.stop_audio_monitoring()  # Stop any existing audio monitoring
        
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
        if effect == "audio":
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
        """Main audio monitoring loop"""
        try:
            # Audio parameters
            sample_rate = 44100
            block_size = 1024
            
            # Use system audio (WASAPI loopback) instead of mic
            def audio_callback(indata, frames, time, status):
                if not self.audio_monitoring:
                    return
                    
                try:
                    # Get audio data from first channel
                    audio_data = indata[:, 0] if indata.shape[1] > 1 else indata.flatten()
                    
                    # Calculate RMS (Root Mean Square) for volume
                    rms = np.sqrt(np.mean(audio_data**2))
                    
                    # Apply sensitivity scaling
                    sensitivity = self.audio_sensitivity.get()
                    volume = rms * sensitivity * 1000
                    
                    # Clamp to valid range
                    brightness = int(np.clip(volume, 0, 255))
                    
                    # Only send if above threshold to reduce noise
                    if brightness > 15:
                        style = self.audio_style_var.get().replace(" ", "_").lower()
                        self.send_command(f"AUDIO,{brightness},{style}")
                        
                except Exception as e:
                    self.log(f"Audio callback error: {e}")
            
            # Start audio stream with WASAPI loopback for system audio
            try:
                # Try to use WASAPI loopback for system audio
                with sd.InputStream(
                    callback=audio_callback,
                    channels=1,
                    samplerate=sample_rate,
                    blocksize=block_size,
                    dtype=np.float32,
                    device='WASAPI (Shared Mode)',
                    latency='low'
                ):
                    self.log(f"System audio stream started (SR: {sample_rate}, Block: {block_size})")
                    
                    while self.audio_monitoring:
                        time.sleep(0.1)
            except Exception as e:
                self.log(f"WASAPI loopback failed, trying default device: {e}")
                # Fallback to default device if WASAPI fails
                with sd.InputStream(
                    callback=audio_callback,
                    channels=1,
                    samplerate=sample_rate,
                    blocksize=block_size,
                    dtype=np.float32
                ):
                    self.log(f"Fallback audio stream started (SR: {sample_rate}, Block: {block_size})")
                    
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
        # Send test key command with selected style
        style = self.key_style_var.get().replace(" ", "_").lower()
        self.send_command(f"KEY,{style}")
        self.log("Test key press sent")
        
    def turn_off_leds(self):
        self.send_command("OFF")
        self.stop_audio_monitoring()  # Stop audio monitoring when turning off
        self.log("LEDs turned off")
        
    def on_closing(self):
        self.stop_monitoring()
        self.stop_audio_monitoring()  # Stop audio monitoring on close
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