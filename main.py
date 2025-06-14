import serial
import time
import threading
from pynput import keyboard

class LEDController:
    def __init__(self, port='COM7', baudrate=9600):  # Changed to COM7
        try:
            self.arduino = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)  # Wait for Arduino to initialize
            print(f"Connected to Arduino on {port}")
        except serial.SerialException as e:
            print(f"Failed to connect to Arduino: {e}")
            self.arduino = None
    
    def send_command(self, command):
        if self.arduino:
            try:
                self.arduino.write(f"{command}\n".encode())
                print(f"Sent: {command}")
            except Exception as e:
                print(f"Error sending command: {e}")
    
    def close(self):
        if self.arduino:
            self.arduino.close()

class KeyboardMonitor:
    def __init__(self, led_controller):
        self.led_controller = led_controller
        self.last_key_time = 0
        self.idle_threshold = 10  # seconds
        self.is_monitoring = True
        
        # Start monitoring threads
        self.keyboard_thread = threading.Thread(target=self.start_keyboard_listener)
        self.idle_monitor_thread = threading.Thread(target=self.monitor_idle)
        self.notification_thread = threading.Thread(target=self.monitor_notifications)
        
        self.keyboard_thread.daemon = True
        self.idle_monitor_thread.daemon = True
        self.notification_thread.daemon = True
        
    def on_key_press(self, key):
        self.last_key_time = time.time()
        try:
            # Print the actual key pressed
            key_name = key.char if hasattr(key, 'char') and key.char else str(key)
            print(f"Key pressed: {key_name} at {time.strftime('%H:%M:%S')}")
        except AttributeError:
            print(f"Special key pressed: {key} at {time.strftime('%H:%M:%S')}")
        
        self.led_controller.send_command("KEY")
    
    def start_keyboard_listener(self):
        print("Keyboard listener started - try typing something...")
        try:
            with keyboard.Listener(on_press=self.on_key_press) as listener:
                listener.join()
        except Exception as e:
            print(f"Keyboard listener error: {e}")
            print("Note: You might need to run as administrator for global key detection")
    
    def monitor_idle(self):
        was_idle = False
        while self.is_monitoring:
            current_time = time.time()
            if current_time - self.last_key_time > self.idle_threshold:
                if not was_idle:  # Only print once when becoming idle
                    print(f"System idle for {self.idle_threshold} seconds - switching to Knight Rider mode")
                    self.led_controller.send_command("IDLE")
                    was_idle = True
            else:
                if was_idle:  # Only print once when becoming active
                    print("System active - keyboard monitoring resumed")
                    was_idle = False
            time.sleep(1)
    
    def monitor_notifications(self):
        """Simple notification system - you can add custom triggers here"""
        notification_count = 0
        
        while self.is_monitoring:
            try:
                # Example: Trigger notification every 30 seconds (for testing)
                time.sleep(10)
                notification_count += 1
                if notification_count % 2 == 0:  # Every minute
                    print(f"Sample notification #{notification_count//2}")
                    self.led_controller.send_command("NOTIFY")
                    
                # You can add custom notification triggers here:
                # - Check for specific file changes
                # - Monitor network activity
                # - Check for new USB devices
                # - Monitor specific applications
                
            except Exception as e:
                print(f"Error in notification monitoring: {e}")
                time.sleep(5)
    
    def start_monitoring(self):
        print("Starting LED monitoring...")
        print("Press Ctrl+C to stop")
        
        self.keyboard_thread.start()
        self.idle_monitor_thread.start()
        self.notification_thread.start()
        
        # Initialize with idle state
        self.led_controller.send_command("IDLE")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping monitor...")
            self.is_monitoring = False
            self.led_controller.close()

# Manual notification trigger class
class ManualNotificationTrigger:
    def __init__(self, led_controller):
        self.led_controller = led_controller
        
    def trigger_notification(self, message="Manual notification"):
        print(f"Triggering: {message}")
        self.led_controller.send_command("NOTIFY")

def main():
    # Change COM port to match your Arduino connection
    led_controller = LEDController('COM7')  # Updated to COM7
    
    if not led_controller.arduino:
        print("Cannot start without Arduino connection")
        print("Available COM ports:")
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        for port in ports:
            print(f"  {port.device} - {port.description}")
        return
    
    monitor = KeyboardMonitor(led_controller)
    
    # Manual notification trigger (optional)
    manual_trigger = ManualNotificationTrigger(led_controller)
    
    print("Available commands:")
    print("- Type anything to see keyboard detection")
    print("- Notifications will trigger every minute (for demo)")
    print("- Press Ctrl+C to stop")
    print("- If no key events show up, try running as administrator")
    
    monitor.start_monitoring()

if __name__ == "__main__":
    main()