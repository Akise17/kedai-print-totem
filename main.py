import sys
import platform
import os
import threading
import paho.mqtt.client as mqtt
import time
from datetime import datetime
import json
import glob
from escpos.printer import File, Serial
from dotenv import load_dotenv

load_dotenv()

MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_TOPIC_SCANNER = os.getenv("MQTT_TOPIC_SCANNER", "qr_scanned")
MQTT_TOPIC_PRINT = os.getenv("MQTT_TOPIC_PRINT", "print_data")
MQTT_TOPIC_PRINT_RECEIVED = os.getenv("MQTT_TOPIC_PRINT", "print_received")
MQTT_TOPIC_PRINT_COMPLETED = os.getenv("MQTT_TOPIC_PRINT", "print_completed")

OS = platform.system()

if OS == "Linux":
  import evdev
  from evdev import InputDevice, categorize, ecodes, list_devices

  DEVICE_NAME = ["WCH.CN 8\x0f Serial To HID", "BARCODE SCANNER Keyboard Interface"]

  def find_scanner():
      devices = [InputDevice(path) for path in list_devices()]
      for d in devices:
          print(f"[Linux] Found: {d.name} at {d.path}")
          if d.name in DEVICE_NAME:
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
              publish_qr_scanned(barcode)
            barcode = ""
          else:
            barcode += key

  def find_printer_device():
    usb_lp = sorted(glob.glob("/dev/usb/lp*"))
    if usb_lp:
        return ("file", usb_lp[0])

    tty_usb = sorted(glob.glob("/dev/ttyUSB*"))
    if tty_usb:
        return ("serial", tty_usb[0])

    return (None, None)

else:
    print(f"OS {OS} belum didukung!")
    sys.exit(1)

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
    
def on_connect(client, userdata, flags, reason_code, properties=None):
  if reason_code == 0:
      print("[MQTT] Connected successfully!")
      client.subscribe(MQTT_TOPIC_PRINT)
  else:
      print(f"[MQTT] Failed to connect, reason code {reason_code}")

def on_message(client, userdata, msg):
  print(f"[MQTT] Received message on {msg.topic}: {msg.payload.decode()}")

  try:
    data = json.loads(msg.payload.decode())
  except Exception as e:
    print("[MQTT] Invalid JSON:", e)
    return

  if data.get("type") == "print_data":
    print("[PRINT] Processing print job...")
    publish_status(MQTT_TOPIC_PRINT_RECEIVED, "print_received", "Print job received")
    print_data = data.get("printData", {})

    text = (
        "===== RECEIPT =====\n"
        f"User: {print_data.get('userName','')}\n"
        f"Merchant: {print_data.get('merchName','')}\n"
        f"Credit Used: {print_data.get('creditUsed','')}\n"
        f"Remaining: {print_data.get('remainingCredit','')}\n"
        f"Receipt ID: {print_data.get('receiptId','')}\n"
        f"Time: {print_data.get('timestamp','')}\n"
        "===================\n\n"
    )

    try:
        printer = get_printer()
        printer.text(text)
        printer.cut()
        print("[PRINT] Print job sent successfully")
        publish_status(MQTT_TOPIC_PRINT_COMPLETED, "print_completed", "Print job completed successfully")

    except Exception as e:
        print("[PRINT] Error printing:", e)
        publish_status(MQTT_TOPIC_PRINT_COMPLETED, "print_completed", f"Print job failed: {e}", False)

def publish_qr_scanned(qr_code):
  data = {
    "type": "qr_scanned",
    "qrData": qr_code,
    "timestamp": datetime.utcnow().isoformat() + "Z"
  }
  client.publish(MQTT_TOPIC_SCANNER, json.dumps(data))
  print(f"[MQTT] Published QR scan: {data}")

def publish_status(topic, status_type, message, success=True):
  payload = {
      "type": status_type,
      "success": success,
      "message": message,
      "timestamp": datetime.utcnow().isoformat() + "Z"
  }
  client.publish(topic, json.dumps(payload))
  print(f"[MQTT] Published to {topic}: {payload}")

if __name__ == "__main__":
  client = mqtt.Client()
  client.on_connect = on_connect
  client.on_message = on_message

  print(f"[MQTT] Connecting to {MQTT_HOST}:{MQTT_PORT} ...")
  client.connect(MQTT_HOST, MQTT_PORT, 60)
  client.loop_start()

  scanner_thread = threading.Thread(target=listen_scanner, daemon=True)
  scanner_thread.start()

  try:
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    print("\n[MQTT] Stopping...")
  finally:
    client.loop_stop()
    client.disconnect()