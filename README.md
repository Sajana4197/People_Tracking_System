Real-Time People Counter & Tracker

A computer vision application that detects, tracks, and counts people crossing a defined line in real-time video feeds. The system provides both command-line and GUI interfaces with capacity monitoring and data export capabilities.

Features

Real-time Person Detection: Uses YOLOv8 for accurate person detection

Multi-Object Tracking: Tracks multiple people simultaneously with unique IDs

Bidirectional Counting: Counts people entering and exiting across a configurable line

Capacity Monitoring: Alerts when maximum capacity is exceeded

Dual Interface: Command-line (main.py) and GUI (gui_app.py) options

Data Export: Export session data in JSON or text format

Auto-save: Automatic periodic saving of session data

Theme Support: Dark and light theme options in GUI

Configurable Settings: Adjustable detection confidence, line position, and direction

Installation

Install dependencies:

pip install -r requirements.txt

Usage
Command-Line Interface (Simple)

Run the basic version without GUI:

python main.py

Controls:

Press q to quit

Press r to reset counts

GUI Interface (Advanced)

Run the full-featured GUI version:

python gui_app.py

GUI Features:

Interactive controls for all settings

Real-time statistics display

Data export functionality

Theme switching

Auto-save capabilities

Enhanced visualization

Configuration Options
Detection Settings

Confidence Threshold: 0.1 to 0.9 (default: 0.4)

Line Position: Adjustable pixel position for counting line

Line Direction: Horizontal or vertical orientation

Max Capacity: Maximum allowed people inside (default: 10)

Data Management

Auto-save: Automatically save data at regular intervals

Save Interval: 10-3600 seconds (default: 60 seconds)

Export Formats: JSON or plain text

Building Executable

To create a standalone executable using PyInstaller:

Prerequisites for Building
pip install pyinstaller

Build Steps

Build the executable:

pyinstaller gui_app.spec

Locate the built application:

The executable will be in the dist/ folder

Look for: dist/Real Time People Counting & Tracking System/

Run: Real Time People Counting & Tracking System.exe
