import serial
import time

def start_serial(port='/dev/ttyUSB0', baud=9600):
    ser = serial.Serial(port, baud, timeout=1)
    time.sleep(2)
    return ser

def read_line(ser):
    try:
        line = ser.readline().decode(errors='ignore').strip()
        return line
    except:
        return None
