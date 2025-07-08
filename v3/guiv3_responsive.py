import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import serial
import serial.tools.list_ports
import time
import threading
from pynput import keyboard
import random

class LEDControllerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Professional LED Controller v3 - Responsive")
        self.root.geometry("1200x900")
        self.root.configure(bg='#1e1e1e')
        
        # Variables
        self.arduino = None
        self.is_monitoring = False
        self.keyboard_listener = None
        self.monitor_thread = None
        self.last_key_time = 0
        self.current_mode = "Disconnected"
        
        # Custom effect variables
        self.custom_color = "#FF0000"
        self.custom_speed = 50
        self.custom_brightness = 100
        
        # Key reactive effect variables
        self.selected_key_effects = ["ripple", "explosion", "wave", "sparkle"]
        self.key_effect_intensity = 50
        
        self.setup_ui()
        self.refresh_ports()
        
    def setup_ui(self):
        # Main container with scrollbar
        main_container = tk.Frame(self.root, bg='#1e1e1e')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(main_container, bg='#1e1e1e', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#1e1e1e')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel to scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Title
        title_label = tk.Label(scrollable_frame, text="WS2812B LED Controller v3", 
                              bg='#1e1e1e', fg='#00ff00', font=('Arial', 20, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Connection Frame
        conn_frame = self.create_frame(scrollable_frame, "Connection", 0)
        
        # Port selection row
        port_row = tk.Frame(conn_frame, bg='#2b2b2b')
        port_row.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(port_row, text="Select Port:", bg='#2b2b2b', fg='white', 
                font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(port_row, textvariable=self.port_var, width=40, state='readonly')
        self.port_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Connection buttons
        btn_frame = tk.Frame(conn_frame, bg='#2b2b2b')
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_ports, 
                 bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'), 
                 width=12, height=2).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="🔌 Connect", command=self.connect_arduino, 
                 bg='#2196F3', fg='white', font=('Arial', 10, 'bold'), 
                 width=12, height=2).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="❌ Disconnect", command=self.disconnect_arduino, 
                 bg='#f44336', fg='white', font=('Arial', 10, 'bold'), 
                 width=12, height=2).pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = tk.Label(conn_frame, text="Status: Disconnected", 
                                    bg='#2b2b2b', fg='red', font=('Arial', 12, 'bold'))
        self.status_label.pack(pady=10)
        
        # Mode Selection Frame
        mode_frame = self.create_frame(scrollable_frame, "Mode Selection", 1)
        
        # Mode buttons in a grid
        modes = [
            ("🎯 Key Reactive + Notification + Idle", "full"),
            ("⌨️ Key Reactive + Idle", "key_idle"),
            ("⌨️ Key Reactive Only", "key_only"),
            ("💤 Idle Only", "idle_only"),
            ("🔔 Key Reactive + Notification", "key_notify"),
            ("🔔 Notification Only", "notify_only"),
            ("🎨 Custom Effects", "custom")
        ]
        
        mode_btn_frame = tk.Frame(mode_frame, bg='#2b2b2b')
        mode_btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        for i, (text, mode) in enumerate(modes):
            row = i // 2
            col = i % 2
            btn = tk.Button(mode_btn_frame, text=text, command=lambda m=mode: self.set_mode(m), 
                          bg='#3f3f3f', fg='white', font=('Arial', 10, 'bold'),
                          width=30, height=3, relief=tk.RAISED, bd=2)
            btn.grid(row=row, column=col, padx=10, pady=10, sticky='ew')
        
        # Configure grid weights
        mode_btn_frame.columnconfigure(0, weight=1)
        mode_btn_frame.columnconfigure(1, weight=1)
        
        # Key Reactive Effects Frame
        key_frame = self.create_frame(scrollable_frame, "Key Reactive Effects", 2)
        
        # Key effect selection in a grid
        key_effects = [
            ("🌊 Ripple", "ripple"),
            ("💥 Explosion", "explosion"),
            ("🌊 Wave", "wave"),
            ("✨ Sparkle", "sparkle"),
            ("💓 Pulse", "pulse"),
            ("☄️ Comet", "comet"),
            ("🎆 Firework", "firework"),
            ("⚡ Lightning", "lightning")
        ]
        
        self.key_effect_vars = {}
        key_effect_frame = tk.Frame(key_frame, bg='#2b2b2b')
        key_effect_frame.pack(fill=tk.X, padx=10, pady=10)
        
        for i, (text, effect) in enumerate(key_effects):
            row = i // 4
            col = i % 4
            var = tk.BooleanVar(value=effect in self.selected_key_effects)
            self.key_effect_vars[effect] = var
            
            effect_frame = tk.Frame(key_effect_frame, bg='#2b2b2b', relief=tk.RAISED, bd=1)
            effect_frame.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
            
            cb = tk.Checkbutton(effect_frame, text=text, variable=var, 
                              bg='#2b2b2b', fg='white', selectcolor='#4CAF50',
                              font=('Arial', 9, 'bold'), activebackground='#2b2b2b')
            cb.pack(padx=5, pady=5)
        
        # Configure grid weights
        for i in range(4):
            key_effect_frame.columnconfigure(i, weight=1)
        
        # Key effect intensity
        intensity_frame = tk.Frame(key_frame, bg='#2b2b2b')
        intensity_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(intensity_frame, text="🎚️ Effect Intensity:", bg='#2b2b2b', fg='white', 
                font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        
        self.key_intensity_scale = tk.Scale(intensity_frame, from_=1, to=100, orient=tk.HORIZONTAL, 
                                           bg='#2b2b2b', fg='white', highlightthickness=0,
                                           troughcolor='#3f3f3f', activebackground='#4CAF50')
        self.key_intensity_scale.set(self.key_effect_intensity)
        self.key_intensity_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Custom Effects Frame
        custom_frame = self.create_frame(scrollable_frame, "Custom Effects", 3)
        
        # Custom effects buttons
        custom_effects = [
            ("🎨 Solid Color", "solid"),
            ("⏳ Sand Clock", "sandclock"),
            ("🌈 Rainbow", "rainbow"),
            ("💨 Breathing", "breathing"),
            ("🎭 Color Wipe", "colorwipe"),
            ("✨ Sparkle", "sparkle"),
            ("🔥 Fire Effect", "fire"),
            ("🔢 Matrix", "matrix")
        ]
        
        custom_btn_frame = tk.Frame(custom_frame, bg='#2b2b2b')
        custom_btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        for i, (text, effect) in enumerate(custom_effects):
            row = i // 4
            col = i % 4
            btn = tk.Button(custom_btn_frame, text=text, command=lambda e=effect: self.custom_effect(e),
                          bg='#6a4c93', fg='white', font=('Arial', 9, 'bold'),
                          width=18, height=2, relief=tk.RAISED, bd=2)
            btn.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        
        # Configure grid weights
        for i in range(4):
            custom_btn_frame.columnconfigure(i, weight=1)
        
        # Custom Settings Frame
        settings_frame = self.create_frame(scrollable_frame, "Custom Settings", 4)
        
        # Settings in a grid layout
        settings_grid = tk.Frame(settings_frame, bg='#2b2b2b')
        settings_grid.pack(fill=tk.X, padx=10, pady=10)
        
        # Color picker
        color_frame = tk.Frame(settings_grid, bg='#2b2b2b')
        color_frame.grid(row=0, column=0, padx=10, pady=5, sticky='ew')
        
        tk.Label(color_frame, text="🎨 Color:", bg='#2b2b2b', fg='white', 
                font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        
        self.color_button = tk.Button(color_frame, text="  ", bg=self.custom_color, 
                                     width=8, height=2, command=self.choose_color,
                                     relief=tk.RAISED, bd=2)
        self.color_button.pack(side=tk.LEFT)
        
        # Speed control
        speed_frame = tk.Frame(settings_grid, bg='#2b2b2b')
        speed_frame.grid(row=0, column=1, padx=10, pady=5, sticky='ew')
        
        tk.Label(speed_frame, text="⚡ Speed:", bg='#2b2b2b', fg='white', 
                font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        
        self.speed_scale = tk.Scale(speed_frame, from_=1, to=100, orient=tk.HORIZONTAL, 
                                   bg='#2b2b2b', fg='white', highlightthickness=0,
                                   troughcolor='#3f3f3f', activebackground='#4CAF50')
        self.speed_scale.set(self.custom_speed)
        self.speed_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Brightness control
        brightness_frame = tk.Frame(settings_grid, bg='#2b2b2b')
        brightness_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky='ew')
        
        tk.Label(brightness_frame, text="💡 Brightness:", bg='#2b2b2b', fg='white', 
                font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        
        self.brightness_scale = tk.Scale(brightness_frame, from_=10, to=255, orient=tk.HORIZONTAL, 
                                        bg='#2b2b2b', fg='white', highlightthickness=0,
                                        troughcolor='#3f3f3f', activebackground='#4CAF50')
        self.brightness_scale.set(self.custom_brightness)
        self.brightness_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Configure grid weights
        settings_grid.columnconfigure(0, weight=1)
        settings_grid.columnconfigure(1, weight=1)
        
        # Control Frame
        control_frame = self.create_frame(scrollable_frame, "Controls", 5)
        
        # Control buttons
        control_btn_frame = tk.Frame(control_frame, bg='#2b2b2b')
        control_btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(control_btn_frame, text="🔔 Test Notification", command=self.test_notification, 
                 bg='#ff9800', fg='white', font=('Arial', 10, 'bold'),
                 width=15, height=2).pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_btn_frame, text="⌨️ Test Key Press", command=self.test_key_press, 
                 bg='#9c27b0', fg='white', font=('Arial', 10, 'bold'),
                 width=15, height=2).pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_btn_frame, text="❌ Turn Off LEDs", command=self.turn_off_leds, 
                 bg='#f44336', fg='white', font=('Arial', 10, 'bold'),
                 width=15, height=2).pack(side=tk.LEFT, padx=5)
        
        # Log Frame
        log_frame = self.create_frame(scrollable_frame, "Activity Log", 6)
        
        # Log text with scrollbar
        log_text_frame = tk.Frame(log_frame, bg='#2b2b2b')
        log_text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = tk.Text(log_text_frame, height=12, bg='#1e1e1e', fg='#00ff00', 
                               font=('Consolas', 9), relief=tk.SUNKEN, bd=2)
        log_scrollbar = tk.Scrollbar(log_text_frame)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        log_scrollbar.config(command=self.log_text.yview)
        
        self.log("🚀 LED Controller GUI v3 Responsive Started")
        
    def create_frame(self, parent, title, index):
        """Create a styled frame with title"""
        frame = tk.LabelFrame(parent, text=title, bg='#2b2b2b', fg='white', 
                             font=('Arial', 12, 'bold'), relief=tk.RAISED, bd=2)
        frame.pack(fill=tk.X, pady=(0, 15))
        return frame
        
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
            self.log("⚠️ No serial ports found")
            
    def connect_arduino(self):
        if not self.port_var.get():
            messagebox.showerror("Error", "Please select a port")
            return
            
        port_name = self.port_var.get().split(' - ')[0]
        
        try:
            self.arduino = serial.Serial(port_name, 9600, timeout=1)
            time.sleep(2)  # Wait for Arduino to initialize
            self.status_label.config(text=f"Status: Connected to {port_name}", fg='green')
            self.log(f"✅ Connected to Arduino on {port_name}")
            
            # Send initial command to test connection
            self.send_command("IDLE")
            
        except serial.SerialException as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
            self.log(f"❌ Connection failed: {e}")
            
    def disconnect_arduino(self):
        if self.arduino:
            self.stop_monitoring()
            self.arduino.close()
            self.arduino = None
            self.status_label.config(text="Status: Disconnected", fg='red')
            self.log("🔌 Disconnected from Arduino")
            
    def send_command(self, command):
        if self.arduino:
            try:
                self.arduino.write(f"{command}\n".encode())
                self.log(f"📤 Sent: {command}")
            except Exception as e:
                self.log(f"❌ Error sending command: {e}")
        else:
            self.log("⚠️ Arduino not connected")
            
    def set_mode(self, mode):
        if not self.arduino:
            messagebox.showerror("Error", "Please connect to Arduino first")
            return
            
        self.stop_monitoring()
        self.current_mode = mode
        
        mode_names = {
            "full": "🎯 Key Reactive + Notification + Idle",
            "key_idle": "⌨️ Key Reactive + Idle",
            "key_only": "⌨️ Key Reactive Only",
            "idle_only": "💤 Idle Only",
            "key_notify": "🔔 Key Reactive + Notification",
            "notify_only": "🔔 Notification Only",
            "custom": "🎨 Custom Effects"
        }
        
        self.log(f"🎛️ Mode set to: {mode_names.get(mode, mode)}")
        
        if mode == "custom":
            self.log("🎨 Custom mode active. Select an effect from Custom Effects section.")
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
            
        self.log("🚀 Monitoring started")
        
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
                
                # Send key effect command with random effect type
                self.send_random_key_effect()
        
        try:
            self.keyboard_listener = keyboard.Listener(on_press=on_key_press)
            self.keyboard_listener.start()
        except Exception as e:
            self.log(f"❌ Keyboard listener error: {e}")
            
    def send_random_key_effect(self):
        """Send a random key effect command"""
        # Get selected effects
        selected_effects = [effect for effect, var in self.key_effect_vars.items() if var.get()]
        
        if not selected_effects:
            selected_effects = ["ripple"]  # Default effect
            
        # Choose random effect
        effect_type = selected_effects[random.randint(0, len(selected_effects)-1)]
        position = random.randint(0, 59)  # Random position
        
        command = f"KEYEFFECT,{effect_type},{position}"
        self.send_command(command)
        
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
                    
            # Handle notifications (simulated)
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
        
        # Get current settings
        color = self.custom_color
        speed = self.speed_scale.get()
        brightness = self.brightness_scale.get()
        
        # Convert color to RGB
        color = color.lstrip('#')
        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        
        command = f"CUSTOM,{effect},{r},{g},{b},{speed},{brightness}"
        self.send_command(command)
        
        self.log(f"🎨 Custom effect: {effect} (R:{r}, G:{g}, B:{b}, Speed:{speed}, Brightness:{brightness})")
            
    def choose_color(self):
        color = colorchooser.askcolor(title="Choose LED Color")[1]
        if color:
            self.custom_color = color
            self.color_button.config(bg=color)
            
    def test_notification(self):
        self.send_command("NOTIFY")
        self.log("🔔 Test notification sent")
        
    def test_key_press(self):
        self.send_random_key_effect()
        self.log("⌨️ Test key effect sent")
        
    def turn_off_leds(self):
        self.send_command("OFF")
        self.log("❌ LEDs turned off")
        
    def on_closing(self):
        self.stop_monitoring()
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