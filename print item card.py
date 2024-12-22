import serial
import serial.tools.list_ports
import time
from PIL import Image
import os
from datetime import datetime

class ThermalPrinter:
    def __init__(self, port=None, baud_rate=None):
        self.port = port
        self.baud_rate = baud_rate
        self.serial = None
    
    def connect(self):
        try:
            # Close the port if it's already open
            if self.serial and self.serial.is_open:
                self.serial.close()
                time.sleep(1)  # Give the system time to release the port
            
            # Open with extended timeout and different settings
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=2,
                writeTimeout=2,
                dsrdtr=True,  # Enable hardware flow control
                rtscts=True   # Enable hardware flow control
            )
            
            # Toggle DTR to reset device
            self.serial.dtr = False
            time.sleep(0.1)
            self.serial.dtr = True
            
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
    
    def write(self, data):
        if self.serial and self.serial.is_open:
            self.serial.write(data)
            self.serial.flush()  # Ensure all data is written
    
    def initialize(self):
        self.write(b'\x1B\x40')  # ESC @
        time.sleep(0.1)  # Give printer time to initialize
    
    def cut(self):
        self.write(b'\x1D\x56\x00')
    
    def feed_lines(self, lines=1):
        self.write(b'\x1B\x64' + bytes([lines]))
    
    def ping(self):
        """
        Send the DLE EOT command to verify the printer connection.
        Returns True if a response is received, False otherwise.
        """
        try:
            # Send DLE EOT 1 (0x10 0x04 0x01)
            command = b'\x10\x04\x01'
            self.write(command)
            
            # Read response (single byte expected)
            response = self.serial.read(1)
            if response:
                print(f"Printer response: {response.hex()}")
                return True
            else:
                print("No response from printer.")
                return False
        except Exception as e:
            print(f"Ping failed: {e}")
            return False

def manual_connect():
    """Allow manual connection to a specific port and baud rate."""
    print("\n=== Manual Printer Connection ===")
    
    # List available ports
    ports = list(serial.tools.list_ports.comports())
    print("\nAvailable ports:")
    for i, port in enumerate(ports, 1):
        print(f"{i}. {port.device} - {port.description}")
    
    # Allow manual port entry or selection
    port_choice = input("\nEnter port number or full port name (e.g., 'COM5'): ")
    try:
        port_num = int(port_choice)
        if 1 <= port_num <= len(ports):
            port = ports[port_num - 1].device
        else:
            print("Invalid port number")
            return None
    except ValueError:
        port = port_choice
    
    # Get baud rate
    baud_rates = [9600, 19200, 38400, 57600, 115200]
    print("\nCommon baud rates:", ", ".join(map(str, baud_rates)))
    baud_rate = input("Enter baud rate (default: 38400): ")
    baud_rate = int(baud_rate) if baud_rate else 38400
    
    # Try to connect
    printer = ThermalPrinter(port, baud_rate)
    if printer.connect():
        print(f"\nSuccessfully connected to {port} at {baud_rate} baud")
        return printer
    return None

def find_printers():
    """Scan all available serial ports and test for printer connections."""
    found_printers = []
    baud_rates = [9600, 19200, 38400, 57600, 115200]
    available_ports = list(serial.tools.list_ports.comports())
    
    print(f"Found {len(available_ports)} ports to test")
    
    for port in available_ports:
        port_name = port.device
        print(f"\nTesting port: {port_name}")
        print(f"Description: {port.description}")
        
        for baud_rate in baud_rates:
            try:
                print(f"Trying baud rate: {baud_rate}")
                
                printer = ThermalPrinter(port_name, baud_rate)
                if printer.connect():
                    # Use the ping method to test the connection
                    if printer.ping():
                        print(f"Successfully connected to printer at {port_name} (Baud: {baud_rate})")
                        found_printers.append({
                            'port': port_name,
                            'baud': baud_rate,
                            'description': port.description
                        })
                        printer.disconnect()
                        break  # Break the baud rate loop if we found a working rate
                        
                    printer.disconnect()
                    
            except Exception as e:
                print(f"Error on {port_name}: {str(e)}")
                continue
            
            # If we found a printer on this port, move to next port
            if any(p['port'] == port_name for p in found_printers):
                break
    
    return found_printers



def test_printer_connection(printer):
    """Test if a printer connection is working."""
    try:
        # Try to print a space character
        printer.initialize()
        printer.write(b' ')
        time.sleep(0.1)
        return True
    except:
        return False
    
# [Previous functions remain the same: get_image_path, get_text_content, get_info_details, 
# print_image, print_text, print_info remain unchanged]


def get_image_path():
    while True:
        path = input("Enter the path to your image file: ")
        if os.path.exists(path):
            return path
        print("File not found. Please enter a valid path.")

def get_text_content():
    print("\n=== Text Input ===")
    text = input("Enter the text you want to print: ")
    size = input("Choose text size (normal/large/small): ").lower()
    while size not in ['normal', 'large', 'small']:
        print("Invalid size. Please choose 'normal', 'large', or 'small'")
        size = input("Choose text size (normal/large/small): ").lower()
    return text, size

def get_info_details():
    print("\n=== Information Input ===")
    info = {}
    print("Enter information (press Enter without input to finish):")
    
    while True:
        key = input("Enter field name (or press Enter to finish): ")
        if not key:
            break
        value = input(f"Enter value for {key}: ")
        info[key] = value
    
    return info

def print_image(printer, image_path):
    try:
        # Basic ESC/POS commands for image printing
        # This is a simplified version - you might need to adjust for your specific printer
        img = Image.open(image_path).convert('L')  # Convert to grayscale
        width = min(512, img.width)  # Most thermal printers are 384 or 512 dots wide
        ratio = width / img.width
        height = int(img.height * ratio)
        img = img.resize((width, height))
        
        # Convert to black and white
        pixels = img.load()
        for y in range(height):
            for x in range(width):
                pixels[x, y] = 0 if pixels[x, y] < 128 else 255
        
        # Send image data to printer
        # This is a basic implementation - you might need to adjust the commands for your printer
        printer.initialize()
        
        # Send image data in 8-dot rows
        for y in range(0, height, 8):
            printer.write(b'\x1B\x2A\x00')
            printer.write(bytes([width & 0xff, width >> 8]))
            
            for x in range(width):
                byte = 0
                for bit in range(min(8, height - y)):
                    if y + bit < height and pixels[x, y + bit] == 0:
                        byte |= 1 << bit
                printer.write(bytes([byte]))
            
            printer.write(b'\x0A')
        printer.feed_lines(4)
        printer.cut()
    except Exception as e:
        print(f"Image printing failed: {e}")

def print_text(printer, text, size='normal'):
    try:
        printer.initialize()
        
        # Set text size
        if size == 'large':
            printer.write(b'\x1D\x21\x11')  # Double width and height
        elif size == 'small':
            printer.write(b'\x1D\x21\x00')  # Normal size
        
        printer.write(text.encode() + b'\n')
        printer.write(b'\x1D\x21\x00')  # Reset text size
        printer.feed_lines(4)
        printer.cut()
    except Exception as e:
        print(f"Text printing failed: {e}")

def print_info(printer, data_dict):
    try:
        printer.initialize()
        printer.write(b'\n=== Information ===\n')
        
        for key, value in data_dict.items():
            line = f"{key}: {value}\n"
            printer.write(line.encode())
        
        timestamp = f"\nPrinted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        printer.write(timestamp.encode())
        printer.feed_lines(4)
        printer.cut()
    except Exception as e:
        print(f"Info printing failed: {e}")


def main():
    print("=== Thermal Printer Utility ===")
    
    # Offer automatic or manual connection
    print("\nConnection options:")
    print("1. Auto-detect printer")
    print("2. Manual connection")
    
    choice = input("Enter choice (1-2): ")
    
    printer = None
    
    if choice == '1':
        # Auto-detection path
        found_printers = find_printers()
        
        if not found_printers:
            print("\nNo printers found automatically. Would you like to try manual connection?")
            if input("Try manual connection? (y/n): ").lower() == 'y':
                printer = manual_connect()
        else:
            print("\nFound printers:")
            for i, p in enumerate(found_printers, 1):
                print(f"\n{i}. Port: {p['port']}")
                print(f"   Baud Rate: {p['baud']}")
                print(f"   Description: {p['description']}")
            
            choice = int(input("\nEnter printer number to use: "))
            if 1 <= choice <= len(found_printers):
                selected = found_printers[choice - 1]
                printer = ThermalPrinter(selected['port'], selected['baud'])
                if not printer.connect():
                    print("Failed to connect to selected printer.")
                    return
    
    elif choice == '2':
        # Manual connection path
        printer = manual_connect()
    
    if not printer:
        print("No printer connected. Exiting.")
        return
    
    # Test printer connection
    print("\nTesting printer connection...")
    if test_printer_connection(printer):
        print("Printer test successful!")
    else:
        print("Printer test failed!")
        return
    
    # Main menu loop
    while True:
        print("\nWhat would you like to do?")
        print("1. Print Image")
        print("2. Print Text")
        print("3. Print Information")
        print("4. Cut Paper")
        print("5. Feed Lines")
        print("6. Exit")
        
        choice = input("Enter your choice (1-6): ")
        
        if choice == '1':
            image_path = get_image_path()
            print_image(printer, image_path)
        
        elif choice == '2':
            text, size = get_text_content()
            print_text(printer, text, size)
        
        elif choice == '3':
            info = get_info_details()
            print_info(printer, info)
        
        elif choice == '4':
            try:
                printer.cut()
                print("Paper cut successfully.")
            except Exception as e:
                print(f"Failed to cut paper: {e}")
        
        elif choice == '5':
            try:
                lines = int(input("Enter the number of lines to feed: "))
                printer.feed_lines(lines)
                print(f"Fed {lines} lines.")
            except ValueError:
                print("Invalid input. Please enter a numeric value.")
            except Exception as e:
                print(f"Failed to feed lines: {e}")
        
        elif choice == '6':
            print("Exiting program...")
            printer.disconnect()
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
