import asyncio
import csv
from datetime import datetime
from bleak import BleakClient, BleakScanner

HR_CHAR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
DEVICE_NAME_HINT = "HR"
CSV_FILE = "hr_data.csv"

latest_hr = None

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

async def main():
    global latest_hr

    device = await find_hr_device()
    if not device:
        print("No HR device found.")
        return

    file = open(CSV_FILE, "a", newline="")
    writer = csv.writer(file)

    if file.tell() == 0:
        writer.writerow(["timestamp", "hr", "energy", "rr_intervals"])

    def notification_handler(sender, data):
        global latest_hr

        parsed = parse_heart_rate_measurement(bytearray(data))
        if not parsed:
            return

        latest_hr = parsed["hr"]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        rr_joined = ";".join(f"{x:.4f}" for x in parsed["rr_intervals"]) if parsed["rr_intervals"] else ""

        print(f"{timestamp} HR:{parsed['hr']}")

        writer.writerow([timestamp, parsed["hr"], parsed["energy"], rr_joined])
        file.flush()

    async with BleakClient(device) as client:
        print("Connected:", client.is_connected)
        await client.start_notify(HR_CHAR_UUID, notification_handler)
        print("Receiving HR notifications... Press Ctrl+C to stop.")

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Stopped by user.")
        finally:
            await client.stop_notify(HR_CHAR_UUID)
            file.close()

if __name__ == "__main__":
    asyncio.run(main())
