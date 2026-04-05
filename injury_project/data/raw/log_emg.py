import serial
import csv
from datetime import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from data.raw.read_emg import parse_emg

# CHANGE THIS if needed
PORT = "/dev/ttyUSB0"
BAUD = 9600

ser = serial.Serial(PORT, BAUD)

filename = f"emg_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

with open(filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["timestamp", "raw", "envelope", "state"])

    print("Logging started... Press CTRL+C to stop")

    try:
        while True:
            line = ser.readline().decode('utf-8').strip()
            parts = line.split(",")

            if len(parts) == 3:
                raw, env, state = parts
                timestamp = datetime.now().strftime("%H:%M:%S.%f")

                writer.writerow([timestamp, raw, env, state])
                print(timestamp, raw, env, state)

    except KeyboardInterrupt:
        print("\nLogging stopped.")
        ser.close()
