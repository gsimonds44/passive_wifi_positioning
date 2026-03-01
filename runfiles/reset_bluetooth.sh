#!/bin/bash

bluetoothctl devices | awk '{print $2}' | xargs -r -n1 bluetoothctl remove >/dev/null 2>&1
bluetoothctl power off >/dev/null 2>&1
sleep 1
bluetoothctl power on >/dev/null 2>&1