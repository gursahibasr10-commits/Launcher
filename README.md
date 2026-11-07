# Launcher

A small PyQt6 desktop launcher inspired by a PlayStation 5 dashboard. It scans Steam installations, lists installed games, and launches a selected Steam game.

## Features
- Reads Steam install path from Windows registry
- Scans `steamapps/*.acf` manifests
- Shows a dashboard-style game library
- Launches the selected game via `steam://run/<appid>`

## Requirements
- Windows 10/11
- Python 3.10+
- PyQt6

## Install
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run
```bash
python main.py
```

## Notes
- The app is primarily intended for Windows since it uses `winreg` and the `start` shell command.
- If Steam is not installed, it falls back to a small sample list of demo games.
