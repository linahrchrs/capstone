import sys
import os
import asyncio
import csv
from datetime import datetime
from collections import deque

import numpy as np
from bleak import BleakClient

# Make project root visible to Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.raw.read_pulse import parse_pulse

ADDRESS = "D6:42:6A:53:B1:12"
HR_CHAR = "00002a37-0000-1000-8000-00805f9b34fb"
CSV_PATH = "data/raw/hr_data.csv"
DURATION_SECONDS = 60

window = deque(maxlen=5)
hr_values = []


def smooth_hr(hr):
    window.append(hr)
    return sum(window) / len(window)


def compute_features(values):
    if not values:
        return None

    arr = np.array(values)
    return {
        "mean_hr": float(np.mean(arr)),
        "min_hr": int(np.min(arr)),
        "max_hr": int(np.max(arr)),
        "variance_hr": float(np.var(arr)),
        "std_hr": float(np.std(arr)),
    }


def ensure_csv_header(path):
    file_exists = os.path.exists(path)
    csv_file = open(path, "a", newline="")
    writer = csv.writer(csv_file)

    if not file_exists:
        writer.writerow(["timestamp", "heart_rate", "smoothed_heart_rate"])

    return csv_file, writer


async def main():
    csv_file, writer = ensure_csv_header(CSV_PATH)

    def hr_callback(sender, data):
        hr = parse_pulse(data)
        if hr is not None:
            smoothed = smooth_hr(hr)
            timestamp = datetime.now().isoformat()

            hr_values.append(hr)

            print(f"{timestamp} | HR: {hr} | Smoothed: {round(smoothed, 2)}")
            writer.writerow([timestamp, hr, round(smoothed, 2)])
            csv_file.flush()

    try:
        async with BleakClient(ADDRESS, timeout=20.0) as client:
            print("Connected:", client.is_connected)

            await client.start_notify(HR_CHAR, hr_callback)
            await asyncio.sleep(DURATION_SECONDS)
            await client.stop_notify(HR_CHAR)

    except Exception as e:
        print("Error:", e)

    finally:
        csv_file.close()

    features = compute_features(hr_values)
    if features:
        print("\nSession features:")
        for key, value in features.items():
            print(f"{key}: {value}")
    else:
        print("\nNo heart rate data collected.")


if __name__ == "__main__":
    asyncio.run(main())
