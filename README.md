# Casambi Bluetooth + HomeKit

- `casambi_test.py` checks that a Casambi network can be controlled over this computer's Bluetooth:
  scans, connects with the network password, lists units, groups and scenes, and can fire a scene.
- `homekit_bridge.py` exposes each Casambi scene to Apple Home as a switch that turns itself off
  after it fires, so "Hey Siri, turn on <scene name>" triggers it. No Home Assistant needed.

The password is typed at a hidden prompt and is never written to disk.

## Setup (Windows)

```powershell
py -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Install Python 3.12 first if `py` isn't found: `winget install Python.Python.3.12`.

## Test the Casambi connection

```powershell
.\venv\Scripts\python.exe casambi_test.py
```

## Run the HomeKit bridge

```powershell
.\venv\Scripts\python.exe homekit_bridge.py
```

First run: pick the Casambi network, type the password, then pair in the Home app
(**+ -> Add Accessory -> More options**, pick "Casambi", enter the code printed in the terminal).
The chosen network is remembered in `bridge_config.json`.

To skip the password prompt, set it for your user once and reopen the terminal:

```powershell
setx CASAMBI_PASSWORD "your-network-password"
```

Options: `--demo` (fake scenes, no Casambi needed), `--device ADDRESS`, `--port N`,
`--ip A.B.C.D` (use if the Home app can't find the bridge, e.g. when the PC has several network adapters).

If scenes change in the Casambi app, restart the bridge. Rename scenes in Apple Home if Siri mishears them.

## Before running

- Windows Bluetooth is on, and the adapter isn't attached to a VM.
- The Casambi phone app is closed (only a few Bluetooth clients can connect at once).
- The PC is within Bluetooth range of a light, stays on, and is on the same network as the iPhone.
- Windows Firewall allows Python on private networks when it asks.
- The network is password protected and runs Evolution firmware.
- A HomePod or Apple TV is needed for Siri away from home.
