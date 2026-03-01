import os
import subprocess
import time
import hashlib
import csv
import asyncio
from bleak import BleakScanner, BleakClient

"""
This script is run simultaneously with the positionTracker iPhone app to collect and label data. 
Launch the iPhone app first, then confirm bluetooth pairing requests on both the iPhone and the laptop.
Stand on the target position indicated in the iPhone app and click the Capture button to send the position data to this script.
A network snapshot will be recorded (with multiple attempts if it did not refresh) and saved to a single .csv file for that position.
An acknowledgment will be sent to the iPhone app once data has been collected and saved.
"""


# BLE device name and service/characteristic UUIDs
smartphone_name = "MyBLEiPhone"
service_uuid = "1234"
characteristic_uuid = "00005678-0000-1000-8000-00805f9b34fb"

# holds the most recent BLE location data (updated dynamically)
latest_location_data = None
location_stuck_counter = 0
ready_for_new_data = True

# load known network hashes once
with open("network_masterlist.csv", "r", newline="") as file:
    reader = csv.reader(file)
    loaded_network_hashes = [row[0] for row in reader]

# reset bluetooth before starting
shellpath = os.path.abspath("reset_bluetooth.sh")
subprocess.run([shellpath])
time.sleep(1)


paired_rssis = []

# collect a snapshot of the rssi for all networks in range
def rssi_snapshot():
    subprocess.run(["nmcli", "device", "wifi", "rescan"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    result = subprocess.run(["nmcli", "-t", "-f", "SSID,CHAN,SIGNAL", "dev", "wifi"], capture_output=True, text=True)
    output = result.stdout.strip()
    networks = [line.split(":") for line in output.split("\n") if line]

    found_network_rssis = []
    found_network_hashes = []

    for ssid, chan, rssi in networks:
        if ssid:
            fingerprint = ssid + chan
            found_network_hashes.append(hashlib.sha256(fingerprint.encode()).hexdigest()) # hash for privacy
            found_network_rssis.append(rssi)

    paired = []
    for loaded_network_hash in loaded_network_hashes:
        if loaded_network_hash in found_network_hashes:
            index = found_network_hashes.index(loaded_network_hash)
            paired.append(found_network_rssis[index])
        else:
            paired.append("unavailable") # if a known network is missing in this scan, mark as unavailable

    return paired


async def find_and_connect():
    global latest_location_data, location_stuck_counter, ready_for_new_data, paired_rssis

    # scan for BLE devices
    devices = await BleakScanner.discover()
    smartphone_device = next((d for d in devices if d.name == smartphone_name), None)

    if not smartphone_device:
        print("SmartPhone not found. Make sure app is running.")
        return

    async with BleakClient(smartphone_device.address) as client: # connect the the smartphone
        print("BLE Connected")
        await asyncio.sleep(1)

        # send acknowledgment ("logged") to smartphone
        async def send_logged():
            if client.is_connected:
                try:
                    await client.write_gatt_char(characteristic_uuid, b"logged", response=False)
                    print("Ready")
                except Exception as e:
                    print("Failed to send 'logged':", e)

        # handle incoming BLE location messages
        async def handle_data(_, data):
            global paired_rssis
            global latest_location_data, location_stuck_counter, ready_for_new_data

            decoded = data.decode('utf-8').strip()

            if not ready_for_new_data:
                print("Ignoring BLE message: still processing previous...")
                return

            print("Received BLE location:", decoded)
            latest_location_data = decoded
            location_stuck_counter = 0
            ready_for_new_data = False

            # retry until a new, unique RSSI snapshot is collected
            max_retries = 50
            retries = 0
            while retries < max_retries:
                new_snapshot = rssi_snapshot()
                if new_snapshot != paired_rssis: # make sure the rssi snapshot has actually updated
                    filename = f"recorded_data/{latest_location_data}.csv"
                    print(f"Saved network snapshot: {filename}")

                    with open(filename, "w", newline="") as file:
                        writer = csv.writer(file)
                        for a, b in zip(loaded_network_hashes, new_snapshot):
                            writer.writerow([a, b]) # save data

                    paired_rssis = new_snapshot
                    await send_logged() # send ack
                    ready_for_new_data = True
                    return

                else:
                    print("RSSI snapshot identical to previous, retrying...")

                retries += 1
                time.sleep(1)

            print("Max retries reached. Snapshot not saved.")
            ready_for_new_data = True

        # subscribe to notifications from the smartphone
        await client.start_notify(characteristic_uuid, handle_data) 
        print("Listening for BLE messages...")

        # keep the event loop alive to continue receiving messages
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(find_and_connect())
