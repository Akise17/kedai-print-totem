import sys
from escpos.printer import Serial

def main():
    if len(sys.argv) < 2:
        print("Usage: python test.py <serial_port>")
        print("Example: python test.py /dev/usb/lp0")
        sys.exit(1)

    port = sys.argv[1]

    try:
        p = Serial(
            devfile=port,
            baudrate=9600,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=1.00
        )

        p.text("Hello, KP-628E!\n")
        p.text("ESC/POS test print OK.\n")
        p.text("--------------------------------\n")
        p.cut()

        print(f"✅ Test print sent to {port}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
