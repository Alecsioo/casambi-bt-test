# Casambi Bluetooth test

Checks that a Casambi network can be controlled over this computer's Bluetooth: scans for the network,
connects with the network password, lists units, groups and scenes, and can fire a scene.
The password is typed at a hidden prompt and is never stored.

## Run (Windows)

```powershell
py -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe casambi_test.py
```

Install Python 3.12 first if `py` isn't found: `winget install Python.Python.3.12`.

## Before running

- Windows Bluetooth is on, and the Bluetooth adapter isn't attached to a VM.
- The Casambi phone app is closed.
- You're within a few metres of one of the lights.
- The network is password protected and runs Evolution firmware.
