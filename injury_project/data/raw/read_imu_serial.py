import serial
import time
from read_imu import parse_imu

SERIAL_PORT = "/dev/ttyUSB0"  # adjust if needed
BAUD_RATE = 115200

def read_imu_stream():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)

    while True:
        try:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue

            data = parse_imu(line)
            if data:
                print(data)   # later → send to pipeline

        except Exception as e:
            print("IMU error:", e)
