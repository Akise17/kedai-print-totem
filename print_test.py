import sys
from escpos.printer import File

def main():
    if len(sys.argv) < 2:
        print("Usage: sudo python3 print_test.py <device_file>")
        print("Example: sudo python3 print_test.py /dev/usb/lp0")
        sys.exit(1)

    port = sys.argv[1]

    try:
        p = File(port)
        p.text("Hello, KP-628E!\n")
        p.text("ESC/POS test print OK.\n")
        p.text("--------------------------------\n")
        p.cut()

        print(f"✅ Test print sent to {port}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
