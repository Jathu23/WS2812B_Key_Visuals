import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import time
import threading
from pynput import keyboard
from collections import deque
import queue

class LEDControllerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced LED Controller - Reactive & Animation Modes")
        self.root.geometry("700x550")
        self.root.configure(bg='#1a1a1a')
        
        # Variables
        self.arduino = None
        self.is_monitoring = False
        self.keyboard_listener = None
        self.monitor_thread = None
        self.last_key_time = 0
        self.current_mode = "Disconnected"
        
        # Animation settings
        self.idle_animation_enabled = True
        self.current_idle_animation = "knight_rider"
        
        # Command optimization
        self.command_queue = queue.Queue()
        self.last_command_time = 0
        self.command_cooldown = 0.05  # 50ms between commands
        self.command_thread = None
        self.is_command_thread_running = False
        
        # Connection optimization
        self.connection_retries = 3
        self.connection_timeout = 5
        
        self.setup_ui()
        self.refresh_ports()
        self.start_command_thread()
        
    def setup_ui(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Connection Frame
        conn_frame = tk.LabelFrame(main_frame, text="Connection", bg='#1a1a1a', fg='#00ff88', 
                                 font=('Arial', 12, 'bold'), relief='ridge', bd=2)
        conn_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Port selection
        tk.Label(conn_frame, text="Port:", bg='#1a1a1a', fg='white', font=('Arial', 10)).grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var, width=35, state='readonly')
        self.port_combo.grid(row=0, column=1, padx=5, pady=10)
        
        tk.Button(conn_frame, text="🔄 Refresh", command=self.refresh_ports, 
                 bg='#4CAF50', fg='white', font=('Arial', 9, 'bold')).grid(row=0, column=2, padx=5, pady=10)
        tk.Button(conn_frame, text="🔗 Connect", command=self.connect_arduino, 
                 bg='#2196F3', fg='white', font=('Arial', 9, 'bold')).grid(row=0, column=3, padx=5, pady=10)
        tk.Button(conn_frame, text="❌ Disconnect", command=self.disconnect_arduino, 
                 bg='#f44336', fg='white', font=('Arial', 9, 'bold')).grid(row=0, column=4, padx=5, pady=10)
        
        # Status
        self.status_label = tk.Label(conn_frame, text="Status: Disconnected", bg='#1a1a1a', fg='#ff4444', 
                                   font=('Arial', 11, 'bold'))
        self.status_label.grid(row=1, column=0, columnspan=5, pady=10)
        
        # Main Mode Selection Frame
        mode_frame = tk.LabelFrame(main_frame, text="🎯 Main Reactive Modes", bg='#1a1a1a', fg='#00ff88', 
                                 font=('Arial', 12, 'bold'), relief='ridge', bd=2)
        mode_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Main mode buttons
        modes = [
            ("⌨️ + 🔔 Keyboard + Notification Reactive", "key_notify"),
            ("⌨️ Keyboard Reactive Only", "key_only"),
            ("🔔 Notification Reactive Only", "notify_only")
        ]
        
        for i, (text, mode) in enumerate(modes):
            btn = tk.Button(mode_frame, text=text, command=lambda m=mode: self.set_mode(m), 
                          bg='#2d4a2d', fg='white', width=40, height=2, font=('Arial', 10, 'bold'))
            btn.pack(pady=8, padx=20)
        
        # Idle Animation Settings Frame
        idle_frame = tk.LabelFrame(main_frame, text="🌟 Idle Animation Settings", bg='#1a1a1a', fg='#ffaa00', 
                                 font=('Arial', 12, 'bold'), relief='ridge', bd=2)
        idle_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Idle animation toggle
        toggle_frame = tk.Frame(idle_frame, bg='#1a1a1a')
        toggle_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(toggle_frame, text="Idle Animation:", bg='#1a1a1a', fg='white', 
                font=('Arial', 11, 'bold')).pack(side=tk.LEFT)
        
        self.idle_var = tk.BooleanVar(value=True)
        self.idle_toggle = tk.Checkbutton(toggle_frame, text="Enable", variable=self.idle_var, 
                                        command=self.toggle_idle_animation, bg='#1a1a1a', fg='#00ff88', 
                                        selectcolor='#333333', font=('Arial', 10, 'bold'))
        self.idle_toggle.pack(side=tk.LEFT, padx=20)
        
        # Animation mode selection
        anim_frame = tk.Frame(idle_frame, bg='#1a1a1a')
        anim_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(anim_frame, text="Animation Mode:", bg='#1a1a1a', fg='white', 
                font=('Arial', 11, 'bold')).pack(side=tk.LEFT)
        
        self.anim_var = tk.StringVar(value="knight_rider")
        animations = [
            ("🚗 Knight Rider", "knight_rider"),
            ("💫 Pulse Wave", "pulse_wave"),
            ("🌈 Rainbow Flow", "rainbow_flow"),
            ("✨ Sparkle Drift", "sparkle_drift"),
            ("🔥 Fire Glow", "fire_glow"),
            ("🌊 Ocean Wave", "ocean_wave")
        ]
        
        for text, anim in animations:
            rb = tk.Radiobutton(anim_frame, text=text, variable=self.anim_var, value=anim,
                              command=self.change_idle_animation, bg='#1a1a1a', fg='white',
                              selectcolor='#333333', font=('Arial', 9))
            rb.pack(side=tk.LEFT, padx=10)
        
        # Control Frame
        control_frame = tk.LabelFrame(main_frame, text="🎮 Controls", bg='#1a1a1a', fg='#ff6600', 
                                    font=('Arial', 12, 'bold'), relief='ridge', bd=2)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        btn_frame = tk.Frame(control_frame, bg='#1a1a1a')
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="🔔 Test Notification", command=self.test_notification, 
                 bg='#ff9800', fg='white', font=('Arial', 10, 'bold'), width=18).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="⌨️ Test Key Press", command=self.test_key_press, 
                 bg='#9c27b0', fg='white', font=('Arial', 10, 'bold'), width=18).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="💡 Turn Off LEDs", command=self.turn_off_leds, 
                 bg='#f44336', fg='white', font=('Arial', 10, 'bold'), width=18).pack(side=tk.LEFT, padx=10)
        
        # Log Frame
        log_frame = tk.LabelFrame(main_frame, text="📋 Activity Log", bg='#1a1a1a', fg='#00ccff', 
                                font=('Arial', 12, 'bold'), relief='ridge', bd=2)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log with scrollbar
        log_container = tk.Frame(log_frame, bg='#1a1a1a')
        log_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = tk.Text(log_container, height=8, bg='#0d1117', fg='#00ff88', 
                              font=('Consolas', 9), relief='sunken', bd=2)
        scrollbar = tk.Scrollbar(log_container, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.log("🚀 Enhanced LED Controller Started - Optimized for Performance!")
        
    def start_command_thread(self):
        """Start the command processing thread"""
        self.is_command_thread_running = True
        self.command_thread = threading.Thread(target=self.command_processor, daemon=True)
        self.command_thread.start()
        
    def command_processor(self):
        """Process commands from queue with proper timing"""
        while self.is_command_thread_running:
            try:
                # Get command from queue with timeout
                command = self.command_queue.get(timeout=0.1)
                
                # Check cooldown
                current_time = time.time()
                if current_time - self.last_command_time < self.command_cooldown:
                    time.sleep(self.command_cooldown - (current_time - self.last_command_time))
                
                # Send command
                self._send_command_direct(command)
                self.last_command_time = time.time()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.log(f"❌ Command processor error: {e}")
                
    def _send_command_direct(self, command):
        """Send command directly to Arduino with error handling"""
        if self.arduino and self.arduino.is_open:
            try:
                # Clear any pending data
                self.arduino.reset_input_buffer()
                self.arduino.reset_output_buffer()
                
                # Send command
                command_bytes = f"{command}\n".encode('utf-8')
                self.arduino.write(command_bytes)
                self.arduino.flush()  # Ensure data is sent
                
                self.log(f"📤 Sent: {command}")
                
            except serial.SerialTimeoutException:
                self.log(f"⚠️ Timeout sending command: {command}")
                self.reconnect_arduino()
            except serial.SerialException as e:
                self.log(f"❌ Serial error: {e}")
                self.reconnect_arduino()
            except Exception as e:
                self.log(f"❌ Error sending command: {e}")
        else:
            self.log("⚠️ Arduino not connected")
        
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
            self.log(f"🔍 Found {len(port_list)} serial ports")
        else:
            self.log("❌ No serial ports found")
            
    def connect_arduino(self):
        if not self.port_var.get():
            messagebox.showerror("Error", "Please select a port")
            return
            
        port_name = self.port_var.get().split(' - ')[0]
        
        for attempt in range(self.connection_retries):
            try:
                self.log(f"🔗 Attempting connection {attempt + 1}/{self.connection_retries}...")
                
                # Close existing connection if any
                if self.arduino:
                    self.arduino.close()
                
                # Create new connection with optimized settings
                self.arduino = serial.Serial(
                    port=port_name,
                    baudrate=9600,
                    timeout=self.connection_timeout,
                    write_timeout=2,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    xonxoff=False,
                    rtscts=False,
                    dsrdtr=False
                )
                
                # Wait for Arduino to initialize
                time.sleep(3)
                
                # Test connection
                self.arduino.write(b"TEST\n")
                time.sleep(0.5)
                
                self.status_label.config(text=f"Status: Connected to {port_name}", fg='#00ff88')
                self.log(f"✅ Connected to Arduino on {port_name}")
                
                # Send initial idle command if enabled
                if self.idle_animation_enabled:
                    self.send_command(f"IDLE_ANIM,{self.current_idle_animation}")
                else:
                    self.send_command("IDLE_OFF")
                
                return  # Success, exit retry loop
                
            except serial.SerialException as e:
                self.log(f"❌ Connection attempt {attempt + 1} failed: {e}")
                if attempt < self.connection_retries - 1:
                    time.sleep(1)  # Wait before retry
                else:
                    messagebox.showerror("Connection Error", f"Failed to connect after {self.connection_retries} attempts: {e}")
                    self.log(f"❌ All connection attempts failed")
                    
    def reconnect_arduino(self):
        """Attempt to reconnect to Arduino"""
        if self.arduino:
            try:
                self.arduino.close()
            except:
                pass
        self.arduino = None
        self.status_label.config(text="Status: Reconnecting...", fg='#ffaa00')
        self.log("🔄 Attempting to reconnect...")
        self.connect_arduino()
            
    def disconnect_arduino(self):
        if self.arduino:
            self.stop_monitoring()
            try:
                self.arduino.close()
            except:
                pass
            self.arduino = None
            self.status_label.config(text="Status: Disconnected", fg='#ff4444')
            self.log("🔌 Disconnected from Arduino")
            
    def send_command(self, command):
        """Queue command for sending (thread-safe)"""
        try:
            self.command_queue.put(command, timeout=0.1)
        except queue.Full:
            self.log(f"⚠️ Command queue full, dropping: {command}")
        except Exception as e:
            self.log(f"❌ Error queuing command: {e}")
            
    def set_mode(self, mode):
        if not self.arduino:
            messagebox.showerror("Error", "Please connect to Arduino first")
            return
            
        self.stop_monitoring()
        self.current_mode = mode
        
        mode_names = {
            "key_notify": "⌨️ + 🔔 Keyboard + Notification Reactive",
            "key_only": "⌨️ Keyboard Reactive Only",
            "notify_only": "🔔 Notification Reactive Only"
        }
        
        self.log(f"🎯 Mode set to: {mode_names.get(mode, mode)}")
        self.start_monitoring(mode)
            
    def start_monitoring(self, mode):
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, args=(mode,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # Start keyboard listener if needed
        if "key" in mode:
            self.start_keyboard_listener()
            
        self.log("🔄 Monitoring started")
        
    def stop_monitoring(self):
        self.is_monitoring = False
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
            
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
            
        self.log("⏹️ Monitoring stopped")
        
    def start_keyboard_listener(self):
        def on_key_press(key):
            if self.is_monitoring:
                self.last_key_time = time.time()
                try:
                    key_name = key.char if hasattr(key, 'char') and key.char else str(key)
                    self.log(f"⌨️ Key pressed: {key_name}")
                except AttributeError:
                    self.log(f"⌨️ Special key pressed: {key}")
                
                self.send_command("KEY")
        
        try:
            self.keyboard_listener = keyboard.Listener(on_press=on_key_press)
            self.keyboard_listener.start()
        except Exception as e:
            self.log(f"❌ Keyboard listener error: {e}")
            
    def monitor_loop(self, mode):
        notification_counter = 0
        last_idle_command_time = 0
        
        # Initialize idle animation if enabled
        if self.idle_animation_enabled:
            self.send_command(f"IDLE_ANIM,{self.current_idle_animation}")
        else:
            self.send_command("IDLE_OFF")
            
        while self.is_monitoring:
            current_time = time.time()
            
            # Handle idle timeout for keyboard modes (reduced frequency)
            if "key" in mode and current_time - self.last_key_time > 5:
                if current_time - last_idle_command_time > 2:  # Only send every 2 seconds
                    if self.idle_animation_enabled:
                        self.send_command(f"IDLE_ANIM,{self.current_idle_animation}")
                    else:
                        self.send_command("IDLE_OFF")
                    last_idle_command_time = current_time
                    
            # Handle notifications (reduced frequency)
            if "notify" in mode:
                notification_counter += 1
                if notification_counter >= 600:  # Every 60 seconds (100ms * 600)
                    # self.send_command("NOTIFY")
                    notification_counter = 0
                    
            time.sleep(0.1)
    
    def toggle_idle_animation(self):
        self.idle_animation_enabled = self.idle_var.get()
        
        if self.idle_animation_enabled:
            self.log(f"✨ Idle animation enabled: {self.current_idle_animation}")
            if self.arduino:
                self.send_command(f"IDLE_ANIM,{self.current_idle_animation}")
        else:
            self.log("⏸️ Idle animation disabled")
            if self.arduino:
                self.send_command("IDLE_OFF")
    
    def change_idle_animation(self):
        self.current_idle_animation = self.anim_var.get()
        self.log(f"🎨 Idle animation changed to: {self.current_idle_animation}")
        
        if self.idle_animation_enabled and self.arduino:
            self.send_command(f"IDLE_ANIM,{self.current_idle_animation}")
        
    def test_notification(self):
        self.send_command("NOTIFY")
        self.log("🔔 Test notification sent")
        
    def test_key_press(self):
        self.send_command("KEY")
        self.log("⌨️ Test key press sent")
        
    def turn_off_leds(self):
        self.send_command("OFF")
        self.log("💡 LEDs turned off")
        
    def on_closing(self):
        self.stop_monitoring()
        self.is_command_thread_running = False
        if self.command_thread:
            self.command_thread.join(timeout=1)
        if self.arduino:
            try:
                self.arduino.close()
            except:
                pass
        self.root.destroy()

def main():
    root = tk.Tk()
    app = LEDControllerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()