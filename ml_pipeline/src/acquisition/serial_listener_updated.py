import serial
import time
import csv
from datetime import datetime

PORT = '/dev/ttyUSB0'
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)

file = open("data_raw.csv", "a", newline="")
writer = csv.writer(file)

# header
if file.tell() == 0:
    writer.writerow(["timestamp", "raw_line", "temp"])

print("Listening...")

while True:
    try:
        line = ser.readline().decode(errors='ignore').strip()

        if line:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

            # ---- PARSE TEMP ----
            temp_value = None
            if line.startswith("TEMP:"):
                try:
                    temp_value = float(line.split(":")[1])
                except:
                    pass

            print(timestamp, line, temp_value)

            writer.writerow([timestamp, line, temp_value])
            file.flush()

    except KeyboardInterrupt:
        print("Stopped")
        break
