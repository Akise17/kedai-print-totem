import sys
import platform

OS = platform.system()

if OS == "Linux":
    import evdev
    from evdev import InputDevice, categorize, ecodes, list_devices

    DEVICE_NAME = "WCH.CN 8 Serial To HID"  # Ganti dengan nama scanner yang sesuai

    def find_scanner():
        devices = [InputDevice(path) for path in list_devices()]
        for device in devices:
            print(f"[Linux] Found: {device.name} at {device.path}")
            if device.name == DEVICE_NAME:
                return device
        return None

    def listen_scanner():
        scanner = find_scanner()
        if not scanner:
            print("Scanner tidak ditemukan di Linux!")
            sys.exit(1)

        print(f"Listening on {scanner.name} ({scanner.path})")
        barcode = ""
        for event in scanner.read_loop():
            if event.type == ecodes.EV_KEY:
                data = categorize(event)
                if data.keystate == 1:  # key down
                    key = evdev.ecodes.KEY[data.scancode].replace("KEY_", "")
                    if key == "ENTER":
                        print("Scanned:", barcode)
                        barcode = ""
                    else:
                        barcode += key

elif OS == "Darwin":  # macOS
    import hid

    VENDOR_ID = 6790   # ganti hasil dari ioreg
    PRODUCT_ID = 57382  # ganti hasil dari ioreg

    def find_scanner():
        for d in hid.enumerate():
            print(f"[macOS] VendorID: {d['vendor_id']}, ProductID: {d['product_id']}, Name: {d['product_string']}")
            if d['vendor_id'] == VENDOR_ID and d['product_id'] == PRODUCT_ID:
                return d
        return None

    def listen_scanner():
      scanner_info = find_scanner()
      if not scanner_info:
          print("Scanner tidak ditemukan di macOS!")
          return

      scanner = hid.Device(path=scanner_info['path'])
      print("Listening on", scanner_info['product_string'])

      barcode = ""
      while True:
        data = scanner.read(64)
        if data:
          print("Data received:", data)
          print(data)

else:
    print(f"OS {OS} belum didukung!")
    sys.exit(1)


if __name__ == "__main__":
    listen_scanner()