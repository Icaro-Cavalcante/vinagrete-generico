import serial

from inference.serial_handler import PORT

print(f"Iniciando escuta pura na {PORT}...")
ser = serial.Serial(PORT, 115200, timeout=1)
ser.reset_input_buffer()

try:
    while True:
        if ser.in_waiting > 0:
            dados = ser.read(ser.in_waiting)
            print(f"[RECEBIDO RAW]: {dados}")
except KeyboardInterrupt:
    ser.close()
    print("\nEncerrado.")
