import subprocess
import time
import hashlib
import csv

"""
This script builds a list of all available wifi networks and saves their fingerprints to "network_masterlist.csv". 
Run this script once before starting data collection, and do not move the laptop after running it.
If any duplicate networks are detected, their ssid will be printed so that they can be added to the blacklist.
This script should be run multiple times to ensure all duplicate networks are detected and to record the largest possible number of networks.
Each execution will likely produce a different list, since many weak networks are on the threshold of detection.
"""


# blacklist networks with multiple instances of the same ssid and channel
ssid_blacklist = []


# force a new scan before fetching data
subprocess.run(["nmcli", "device", "wifi", "rescan"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)  # Allow time for scanning

# get fresh results
result = subprocess.run(["nmcli", "-t", "-f", "SSID,CHAN,SIGNAL", "dev", "wifi"], capture_output=True, text=True)
output = result.stdout.strip()
networks = [line.split(":") for line in output.split("\n") if line]

# compile a list of networks
network_hashes = []
fingerprints = []
for ssid, chan, rssi in networks:
    if ssid:
        if ssid not in ssid_blacklist:
            fingerprint = ssid+chan
            network_hashes.append(hashlib.sha256(fingerprint.encode()).hexdigest()) # hash for privacy
            if fingerprint in fingerprints:
                print(str(ssid)) # print duplicate networks, so that they can be blacklisted
            fingerprints.append(fingerprint)

if len(network_hashes) == len(set(network_hashes)): # check to make sure there are no duplicate networks

    # save the list of network hashes
    print(str(len(network_hashes))+" networks saved to file.")
    print("Multiple runs may be needed to identify and blacklist all duplicate networks.")
    with open("network_masterlist.csv", "w", newline = "") as file:
        writer = csv.writer(file)
        for item in network_hashes:
            writer.writerow([item])

else:
    print("The duplicate networks above need to be blacklisted.")










