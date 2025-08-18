from escpos.printer import Serial

p = Serial(devfile='/dev/ttyUSB0',
           baudrate=9600,
           bytesize=8,
           parity='N',
           stopbits=1,
           timeout=1.00)

p.text("Hello, KP-628E!\n")
p.text("ESC/POS test print OK.\n")
p.text("--------------------------------\n")
p.cut()
