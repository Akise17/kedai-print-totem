import sys
from escpos.printer import File, Serial
import glob

def find_printer_device():
    usb_lp = sorted(glob.glob("/dev/usb/lp*"))
    if usb_lp:
        return ("file", usb_lp[0])

    tty_usb = sorted(glob.glob("/dev/ttyUSB*"))
    if tty_usb:
        return ("serial", tty_usb[0])

    return (None, None)

def get_printer():
  mode, device = find_printer_device()
  if not device:
      raise RuntimeError("No printer device found!")

  print(f"[PRINTER] Using {mode.upper()} mode on {device}")

  if mode == "file":
      return File(device)
  elif mode == "serial":
      return Serial(
          devfile=device,
          baudrate=9600,
          bytesize=8,
          parity='N',
          stopbits=1,
          timeout=1.00
      )


def main():
  try:
    p = get_printer()
    p.text("Hello, KP-628E!\n")
    p.text("ESC/POS test print OK.\n")
    p.text("--------------------------------\n")
    p.cut()

    print("✅ Test print sent successfully")

  except Exception as e:
    print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
