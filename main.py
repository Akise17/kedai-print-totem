import sys
import platform
import os
import dotenv
import paho.mqtt.client as mqtt
import time
import datetime

from dotenv import load_dotenv

load_dotenv()

MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_TOPIC_SCANNER = os.getenv("MQTT_TOPIC_SCANNER", "scanner/data")
MQTT_TOPIC_PRINT = os.getenv("MQTT_TOPIC_PRINT", "print")

OS = platform.system()

if OS == "Linux":
    import evdev
    from evdev import InputDevice, categorize, ecodes, list_devices

    DEVICE_NAME = "WCH.CN 8\x0f Serial To HID"  # Ganti dengan nama scanner yang sesuai

    def find_scanner():
        devices = [InputDevice(path) for path in list_devices()]
        for d in devices:
            print(f"[Linux] Found: {d.name} at {d.path}")
            if d.name == DEVICE_NAME:
                return d
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
                        if barcode:
                            print("Scanned:", barcode)
                            publish_qr_scanned(client, barcode)  # kirim via MQTT
                        barcode = ""
                    else:
                        barcode += key

elif OS == "Darwin":  # macOS
  import hid
  from dotenv import load_dotenv
  import os

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

    while True:
      data = scanner.read(64)
      if data:
        # misal parse ke string QR
        qr_code = "".join([chr(x) for x in data if x > 0])
        if qr_code.strip():
          print("Scanned:", qr_code)
          publish_qr_scanned(client, qr_code)

else:
    print(f"OS {OS} belum didukung!")
    sys.exit(1)

def on_connect(client, userdata, flags, reason_code, properties=None):
  if reason_code == 0:
      print("[MQTT] Connected successfully!")
      client.subscribe("print")
  else:
      print(f"[MQTT] Failed to connect, reason code {reason_code}")

def on_message(client, userdata, msg):
  print(f"[MQTT] Received message on {msg.topic}: {msg.payload.decode()}")

def publish_qr_scanned(client, qr_code):
    data = {
      "type": "qr_scanned",
      "qrData": qr_code,
      "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    client.publish("print", json.dumps(data))
    print(f"[MQTT] Published QR scan: {data}")

if __name__ == "__main__":
  client = mqtt.Client()
  client.on_connect = on_connect
  client.on_message = on_message

  print(f"[MQTT] Connecting to {MQTT_HOST}:{MQTT_PORT} ...")
  client.connect(MQTT_HOST, MQTT_PORT, 60)
  client.loop_start()

  try:
    while True:
      time.sleep(1)  # keep main thread alive
  except KeyboardInterrupt:
    print("\n[MQTT] Stopping...")
  finally:
    client.loop_stop()
    client.disconnect()