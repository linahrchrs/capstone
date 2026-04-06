import asyncio
import csv
import os
import time
from datetime import datetime

from bleak import BleakClient, BleakScanner
from ml_pipeline.src.acquisition.serial_listener import start_serial, read_line

# ---------- Arduino ----------
PORT = "/dev/ttyUSB0"
BAUD = 9600

# ---------- BLE ----------
HR_CHAR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
DEVICE_NAME_HINT = "HR"

latest_hr = None


def parse_arduino_line(line):
    data = {}
    try:
        parts = line.strip().split(",")
        for p in parts:
            key, value = p.split(":", 1)
            if value == "NaN":
                data[key.lower()] = None
            else:
                data[key.lower()] = float(value)
        return data
    except Exception:
        return None


def parse_heart_rate_measurement(data: bytearray):
    if len(data) < 2:
        return None

    flags = data[0]
    hr_16bit = flags & 0x01
    energy_present = (flags >> 3) & 0x01
    rr_present = (flags >> 4) & 0x01

    index = 1

    if hr_16bit:
        if len(data) < 3:
            return None
        hr = int.from_bytes(data[index:index + 2], byteorder="little")
        index += 2
    else:
        hr = data[index]
        index += 1

    energy = None
    if energy_present and len(data) >= index + 2:
        energy = int.from_bytes(data[index:index + 2], byteorder="little")
        index += 2

    rr_intervals = []
    if rr_present:
        while len(data) >= index + 2:
            rr_raw = int.from_bytes(data[index:index + 2], byteorder="little")
            rr_intervals.append(rr_raw / 1024.0)
            index += 2

    return {"hr": hr, "energy": energy, "rr_intervals": rr_intervals}


async def find_hr_device():
    print("Scanning for HR belt...")
    devices = await BleakScanner.discover(timeout=8.0)

    for d in devices:
        name = d.name or ""
        print(f"Found: {name} [{d.address}]")
        if DEVICE_NAME_HINT.lower() in name.lower():
            print(f"Using device: {name} [{d.address}]")
            return d

    return None


def get_session_info():
    valid_labels = {"rest", "walking", "intense"}

    while True:
        label = input("Enter session label (rest / walking / intense): ").strip().lower()
        if label in valid_labels:
            break
        print("Invalid label. Please choose: rest, walking, or intense.")

    session_name = input("Optional session name (press Enter to skip): ").strip()

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = os.path.join("ml_pipeline", "data", "raw", label)
    os.makedirs(folder, exist_ok=True)

    if session_name:
        filename = f"{label}_{session_name}_{timestamp_str}.csv"
    else:
        filename = f"{label}_{timestamp_str}.csv"

    csv_path = os.path.join(folder, filename)
    return label, csv_path


async def record_session():
    global latest_hr

    label, csv_file = get_session_info()
    print(f"Data will be saved to: {csv_file}")

    ser = start_serial(PORT, BAUD)

    device = await find_hr_device()
    if not device:
        print("No HR device found.")
        ser.close()
        return

    with open(csv_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            "timestamp",
            "label",
            "temp",
            "emg_raw",
            "emg_env",
            "emg_state",
            "ax",
            "ay",
            "az",
            "hr"
        ])

        def notification_handler(sender, data):
            global latest_hr
            parsed = parse_heart_rate_measurement(bytearray(data))
            if parsed:
                latest_hr = parsed["hr"]

        async with BleakClient(device) as client:
            print("Connected to HR belt:", client.is_connected)
            await client.start_notify(HR_CHAR_UUID, notification_handler)

            ser.reset_input_buffer()
            time.sleep(0.2)

            print("Recording started. Press Ctrl+C to stop.")

            try:
                while True:
                    line = read_line(ser)

                    if line:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                        parsed = parse_arduino_line(line)

                        if parsed and latest_hr is not None:
                            row = [
                                timestamp,
                                label,
                                parsed.get("temp"),
                                parsed.get("emg_raw"),
                                parsed.get("emg_env"),
                                parsed.get("emg_state"),
                                parsed.get("ax"),
                                parsed.get("ay"),
                                parsed.get("az"),
                                latest_hr
                            ]

                            print(
                                f"{timestamp} | "
                                f"LABEL:{label} "
                                f"TEMP:{parsed.get('temp')} "
                                f"EMG_ENV:{parsed.get('emg_env')} "
                                f"AX:{parsed.get('ax')} "
                                f"AY:{parsed.get('ay')} "
                                f"AZ:{parsed.get('az')} "
                                f"HR:{latest_hr}"
                            )

                            writer.writerow(row)
                            file.flush()

                    await asyncio.sleep(0.01)

            except KeyboardInterrupt:
                print("\nRecording stopped.")
                print(f"Saved to: {csv_file}")
            finally:
                await client.stop_notify(HR_CHAR_UUID)
                ser.close()


if __name__ == "__main__":
    asyncio.run(record_session())
