import serial
import time
import csv
from datetime import datetime

PORT = '/dev/ttyUSB0'
BAUD = 9600

def parse_arduino_line(line):
    data = {}
    try:
        parts = line.strip().split(',')
        for p in parts:
            key, value = p.split(':', 1)
            if value == "NaN":
                data[key.lower()] = None
            else:
                data[key.lower()] = float(value)
        return data
    except:
        return None

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)

file = open("sensors_data.csv", "a", newline="")
writer = csv.writer(file)

# header
if file.tell() == 0:
    writer.writerow([
        "timestamp",
        "temp",
        "emg_raw",
        "emg_env",
        "emg_state",
        "ax",
        "ay",
        "az"
    ])

print("Listening to Arduino...")

while True:
    try:
        line = ser.readline().decode(errors='ignore').strip()

        if line:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            parsed = parse_arduino_line(line)

            print(timestamp, line)

            if parsed:
                writer.writerow([
                    timestamp,
                    parsed.get("temp"),
                    parsed.get("emg_raw"),
                    parsed.get("emg_env"),
                    parsed.get("emg_state"),
                    parsed.get("ax"),
                    parsed.get("ay"),
                    parsed.get("az"),
                ])
                file.flush()

    except KeyboardInterrupt:
        print("Stopped")
        break
