from escpos import printer
from escpos.exceptions import USBNotFoundError
from PIL import Image
import usb.core
import usb.util
import os
from datetime import datetime
from serial.tools import list_ports

class ThermalPrinter:
    def __init__(self):
        self.printer = None
    
    def connect_usb(self, vendor_id=None, product_id=None):
        try:
            if vendor_id is None or product_id is None:
                devices = self.list_usb_printers()
                if not devices:
                    raise USBNotFoundError("No USB printers found")
                vendor_id = devices[0]['vendor_id']
                product_id = devices[0]['product_id']
            
            self.printer = printer.Usb(vendor_id, product_id)
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def connect_serial(self, port, baud_rate=38400):
        try:
            self.printer = printer.Serial(devfile=port, baudrate=baud_rate)
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    @staticmethod
    def list_usb_printers():
        """Find all USB printers connected to the system."""
        printers = []
        devices = usb.core.find(find_all=True)
        for device in devices:
            if device.bDeviceClass == 7:
                printers.append({
                    'vendor_id': device.idVendor,
                    'product_id': device.idProduct,
                    'manufacturer': usb.util.get_string(device, device.iManufacturer),
                    'product': usb.util.get_string(device, device.iProduct)
                })
        return printers

    @staticmethod
    def list_serial_ports():
        """List available COM ports."""
        ports = list_ports.comports()
        return [port.device for port in ports]
    
    def disconnect(self):
        """Disconnect the printer and clean up resources."""
        if self.printer:
            try:
                self.printer.close()
            except Exception as e:
                print(f"Failed to properly close the connection: {e}")
            self.printer = None

    
    def print_text(self, text, size='normal'):
        if not self.printer:
            print("Printer not connected")
            return
        
        try:
            if size == 'large':
                self.printer.set(width=2, height=2)
            elif size == 'small':
                self.printer.set(width=1, height=1)
            else:
                self.printer.set(width=1, height=1)
            
            self.printer.text(text + '\n')
            self.printer.set(width=1, height=1)
            self.printer.cut()
        except Exception as e:
            print(f"Failed to print text: {e}")
    
    def print_image(self, image_path):
        if not self.printer:
            print("Printer not connected")
            return
        
        try:
            self.printer.image(Image.open(image_path))
            self.printer.cut()
        except Exception as e:
            print(f"Failed to print image: {e}")
    
    def print_info(self, data_dict):
        if not self.printer:
            print("Printer not connected")
            return
        
        try:
            self.printer.text("=== Information ===\n")
            for key, value in data_dict.items():
                self.printer.text(f"{key}: {value}\n")
            
            self.printer.text(f"\nPrinted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.printer.cut()
        except Exception as e:
            print(f"Failed to print info: {e}")
    
    def feed_lines(self, lines=1):
        if not self.printer:
            print("Printer not connected")
            return
        
        try:
            self.printer.text('\n' * lines)
        except Exception as e:
            print(f"Failed to feed lines: {e}")
            
    def cut(self):
        if not self.printer:
            print("Printer not connected")
            return
        
        try:
            self.printer.cut()
        except Exception as e:
            print(f"Failed to cut: {e}")

def main():
    print("=== Thermal Printer Utility ===")
    thermal_printer = ThermalPrinter()
    
    print("\nConnection options:")
    print("1. USB connection")
    print("2. Serial connection")
    
    choice = input("Enter choice (1-2): ")
    
    if choice == '1':
        usb_printers = thermal_printer.list_usb_printers()
        if not usb_printers:
            print("No USB printers found!")
            return
        
        print("\nFound USB printers:")
        for i, p in enumerate(usb_printers, 1):
            print(f"\n{i}. Manufacturer: {p['manufacturer']}")
            print(f"   Product: {p['product']}")
            print(f"   Vendor ID: {hex(p['vendor_id'])}")
            print(f"   Product ID: {hex(p['product_id'])}")
        
        printer_num = int(input("\nSelect printer number: "))
        selected_printer = usb_printers[printer_num - 1]
        
        if not thermal_printer.connect_usb(selected_printer['vendor_id'], 
                                           selected_printer['product_id']):
            print("Failed to connect to printer")
            return
    
    elif choice == '2':
        serial_ports = thermal_printer.list_serial_ports()
        if not serial_ports:
            print("No serial ports found!")
            return
        
        print("\nAvailable COM ports:")
        for i, port in enumerate(serial_ports, 1):
            print(f"{i}. {port}")
        
        port_num = int(input("\nSelect COM port number: "))
        selected_port = serial_ports[port_num - 1]
        
        baud_rate = input("Enter baud rate (default: 38400): ")
        baud_rate = int(baud_rate) if baud_rate else 38400
        
        if not thermal_printer.connect_serial(selected_port, baud_rate):
            print("Failed to connect to printer")
            return
    
    else:
        print("Invalid choice")
        return
    
    print("\nPrinter connected successfully!")
    
    # Main menu loop
    while True:
        print("\nWhat would you like to do?")
        print("1. Print Image")
        print("2. Print Text")
        print("3. Print Information")
        print("4. Feed Lines")
        print("5. Cut")
        print("6. Exit")
        
        choice = input("Enter your choice (1-6): ")
        
        if choice == '1':
            image_path = get_image_path()
            thermal_printer.print_image(image_path)
        
        elif choice == '2':
            text, size = get_text_content()
            thermal_printer.print_text(text, size)
        
        elif choice == '3':
            info = get_info_details()
            thermal_printer.print_info(info)
        
        elif choice == '4':
            try:
                lines = int(input("Enter the number of lines to feed: "))
                thermal_printer.feed_lines(lines)
            except ValueError:
                print("Invalid input. Please enter a number.")
        
        elif choice == '5':
            thermal_printer.cut()
        
        elif choice == '6':
            print("Exiting program...")
            thermal_printer.disconnect()
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
