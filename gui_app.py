# gui_app.py
import sys
import cv2
import json
import os
import time
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QSpinBox, QSlider, QComboBox, QGroupBox, QFileDialog,
    QMessageBox, QStatusBar, QMenuBar, QMenu, QStyle, QSplashScreen, QProgressDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap, QAction

# Import detection/tracking modules (must exist in project)
from detector import PersonDetector
from tracker import MultiObjectTracker
from counter import PeopleCounter
from visualizer import Visualizer


class PeopleCounterApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Real-Time People Counter & Tracker")
        self.resize(1200, 800)

        # App state
        self.is_running = False
        self.cap = None
        self.detector = None
        self.tracker = None
        self.counter = None
        self.visualizer = None
        self.session_start_time = None

        # Settings (default)
        self.settings = {
            'camera_index': 0,
            'max_capacity': 10,
            'line_position': 240,
            'direction': 'horizontal',
            'confidence': 0.4,
            'line_color': (0, 0, 255),
            'auto_save': True,
            'save_interval': 60,
            'theme': "Dark"
        }
        self.last_save = time.time()
        self.load_settings()

        # Themes
        self.dark_theme = """
            QMainWindow { background-color: #2c3e50; }
            QLabel { color: white; font-size: 13px; }
            QGroupBox {
                border: 2px solid #34495e;
                border-radius: 8px;
                margin-top: 10px;
                color: #ecf0f1;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:pressed { background-color: #1f618d; }
            QSpinBox, QComboBox, QSlider {
                background-color: #34495e;
                color: white;
                border-radius: 4px;
                padding: 4px;
            }
            QStatusBar { background-color: #34495e; color: white; }
        """

        self.light_theme = """
            QMainWindow { background-color: #ecf0f1; }
            QLabel { color: black; font-size: 13px; }
            QGroupBox {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                color: #2c3e50;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:pressed { background-color: #1f618d; }
            QSpinBox, QComboBox, QSlider {
                background-color: #ffffff;
                color: black;
                border-radius: 4px;
                padding: 4px;
            }
            QStatusBar { background-color: #bdc3c7; color: black; }
        """

        # Central widget and layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # --- Video feed panel ---
        self.video_label = QLabel("Camera Feed Will Appear Here\nClick 'Start Counting'")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; color: white; font-size: 14px;")
        layout.addWidget(self.video_label, 3)

        # --- Control panel ---
        controls = QVBoxLayout()
        layout.addLayout(controls, 1)

        controls.addWidget(self.create_settings_group())
        controls.addWidget(self.create_stats_group())
        controls.addWidget(self.create_buttons_group())
        controls.addStretch(1)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

        # Menu bar
        self.create_menu()

        # Timer for video updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        # Track stats
        self.count_in = 0
        self.count_out = 0
        self.current_inside = 0
        self.active_tracks = 0
        self.over_capacity = False

        # Apply saved theme
        self.change_theme(self.settings.get("theme", "Dark"))

    # ---------------- UI builders ----------------
    def create_settings_group(self):
        group = QGroupBox("Settings")
        vbox = QVBoxLayout(group)

        # Max capacity
        self.capacity_spin = QSpinBox()
        self.capacity_spin.setRange(1, 1000)
        self.capacity_spin.setValue(self.settings['max_capacity'])
        self.capacity_spin.valueChanged.connect(self.update_max_capacity)
        vbox.addWidget(QLabel("Max Capacity:"))
        vbox.addWidget(self.capacity_spin)

        # Line position
        self.line_slider = QSlider(Qt.Orientation.Horizontal)
        self.line_slider.setRange(50, 600)
        self.line_slider.setValue(self.settings['line_position'])
        self.line_slider.valueChanged.connect(self.update_line_position)
        vbox.addWidget(QLabel("Line Position:"))
        vbox.addWidget(self.line_slider)

        # Direction
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["horizontal", "vertical"])
        self.direction_combo.setCurrentText(self.settings['direction'])
        self.direction_combo.currentTextChanged.connect(self.update_direction)
        vbox.addWidget(QLabel("Line Direction:"))
        vbox.addWidget(self.direction_combo)

        # Confidence
        self.conf_slider = QSlider(Qt.Orientation.Horizontal)
        self.conf_slider.setRange(1, 9)
        self.conf_slider.setValue(int(self.settings['confidence'] * 10))
        self.conf_slider.valueChanged.connect(self.update_confidence)
        vbox.addWidget(QLabel("Detection Confidence:"))
        vbox.addWidget(self.conf_slider)

        # Auto-save interval
        self.save_interval_spin = QSpinBox()
        self.save_interval_spin.setRange(10, 3600)  # between 10s and 1 hour
        self.save_interval_spin.setValue(self.settings.get('save_interval', 60))
        self.save_interval_spin.valueChanged.connect(self.update_save_interval)
        vbox.addWidget(QLabel("Auto-Save Interval (seconds):"))
        vbox.addWidget(self.save_interval_spin)

        # Theme switcher
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setCurrentText(self.settings.get("theme", "Dark"))
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        vbox.addWidget(QLabel("Theme:"))
        vbox.addWidget(self.theme_combo)

        return group

    def create_stats_group(self):
        group = QGroupBox("Statistics")
        vbox = QVBoxLayout(group)

        self.lbl_in = QLabel("People Entered: 0")
        self.lbl_out = QLabel("People Exited: 0")
        self.lbl_inside = QLabel("Currently Inside: 0")
        self.lbl_tracks = QLabel("Active Tracks: 0")
        self.lbl_status = QLabel("Status: Normal")
        self.lbl_session = QLabel("Session Time: 00:00:00")

        for lbl in [self.lbl_in, self.lbl_out, self.lbl_inside, self.lbl_tracks, self.lbl_status, self.lbl_session]:
            lbl.setStyleSheet("font-size: 12px;")
            vbox.addWidget(lbl)

        return group

    def create_buttons_group(self):
        group = QGroupBox("Controls")
        vbox = QVBoxLayout(group)

        # Start/Stop button (icon + text)
        self.start_button = QPushButton(" Start Counting")
        self.start_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.start_button.setToolTip("Icon: Play — Start Counting")
        self.start_button.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        self.start_button.clicked.connect(self.toggle_counting)
        vbox.addWidget(self.start_button)

        # Reset button (icon + text)
        self.reset_button = QPushButton(" Reset Counts")
        self.reset_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.reset_button.setToolTip("Icon: Reload — Reset Counts")
        self.reset_button.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold;")
        self.reset_button.clicked.connect(self.reset_counts)
        vbox.addWidget(self.reset_button)

        # Export button (icon + text)
        self.export_button = QPushButton(" Export Data")
        self.export_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.export_button.setToolTip("Icon: Save — Export Data")
        self.export_button.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        self.export_button.clicked.connect(self.export_data)
        vbox.addWidget(self.export_button)

        return group

    def create_menu(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        file_menu = QMenu("File", self)
        menubar.addMenu(file_menu)

        export_action = QAction("Export Data", self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)

        import_settings_action = QAction("Import Settings", self)
        import_settings_action.triggered.connect(self.import_settings)
        file_menu.addAction(import_settings_action)

        export_settings_action = QAction("Export Settings", self)
        export_settings_action.triggered.connect(self.export_settings)
        file_menu.addAction(export_settings_action)

        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = QMenu("Help", self)
        menubar.addMenu(help_menu)
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    # ---------------- Settings Updates ----------------
    def update_max_capacity(self):
        self.settings['max_capacity'] = self.capacity_spin.value()
        if self.counter:
            self.counter.max_capacity = self.settings['max_capacity']
        self.save_settings()

    def update_line_position(self):
        self.settings['line_position'] = self.line_slider.value()
        if self.counter and self.visualizer:
            self.counter.line_position = self.settings['line_position']
            self.visualizer.line_position = self.settings['line_position']
        self.save_settings()

    def update_direction(self):
        self.settings['direction'] = self.direction_combo.currentText()
        if self.counter and self.visualizer:
            self.counter.direction = self.settings['direction']
            self.visualizer.direction = self.settings['direction']
        self.save_settings()

    def update_confidence(self):
        self.settings['confidence'] = self.conf_slider.value() / 10.0
        if self.detector:
            self.detector.confidence = self.settings['confidence']
        self.save_settings()

    def update_save_interval(self):
        self.settings['save_interval'] = self.save_interval_spin.value()
        self.save_settings()


    def change_theme(self, theme_name):
        # Apply stylesheet and save selection
        if theme_name == "Dark":
            self.setStyleSheet(self.dark_theme)
            self.settings["theme"] = "Dark"
        else:
            self.setStyleSheet(self.light_theme)
            self.settings["theme"] = "Light"
        self.save_settings()

    # ---------------- Video Handling ----------------
    def toggle_counting(self):
        if not self.is_running:
            self.start_counting()
        else:
            self.stop_counting()

    def start_counting(self):
        # Show loading dialog
        loading = QProgressDialog("Starting camera...", None, 0, 0, self)
        loading.setWindowTitle("Please wait")
        loading.setWindowModality(Qt.WindowModality.ApplicationModal)
        loading.setAutoClose(True)
        loading.show()
        QApplication.processEvents()

        self.cap = cv2.VideoCapture(self.settings['camera_index'])
        if not self.cap.isOpened():
            loading.close()
            QMessageBox.critical(self, "Error", "Could not open camera")
            return

        # Set camera resolution (optional)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Initialize components
        self.detector = PersonDetector(confidence=self.settings['confidence'])
        self.tracker = MultiObjectTracker()
        self.counter = PeopleCounter(
            line_position=self.settings['line_position'],
            direction=self.settings['direction'],
            max_capacity=self.settings['max_capacity']
        )
        self.visualizer = Visualizer(
            line_position=self.settings['line_position'],
            direction=self.settings['direction']
        )

        # Close loading dialog
        loading.close()

        self.session_start_time = time.time()
        self.is_running = True
        # Update start button (text + icon)
        self.start_button.setText(" Stop Counting")
        self.start_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.start_button.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold;")
        self.status.showMessage("Counting in progress...")
        self.timer.start(30)

    def stop_counting(self):
        self.is_running = False
        self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None
        # Update start button back to Start look
        self.start_button.setText(" Start Counting")
        self.start_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.start_button.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        self.status.showMessage("Stopped")
        self.video_label.setText("Camera Feed Stopped\nClick 'Start Counting'")

    def update_frame(self):
        if not self.cap:
            return
        ret, frame = self.cap.read()
        if not ret:
            return

        # Main pipeline (detection, tracking, counting)
        detections = self.detector.detect(frame)
        tracked_objects = self.tracker.update(frame, detections)

        active_ids = [obj["id"] for obj in tracked_objects]
        for obj in tracked_objects:
            self.counter.check_crossing(obj["id"], obj["bbox"])
        self.counter.cleanup_lost_tracks(active_ids)

        # Stats
        self.count_in, self.count_out = self.counter.get_counts()
        self.over_capacity, self.current_inside = self.counter.is_over_capacity()
        self.active_tracks = len(tracked_objects)

        # Visualization overlay
        frame = self.visualizer.draw(frame, tracked_objects,
                                     self.count_in, self.count_out,
                                     self.over_capacity, self.current_inside)

        # Convert frame to QPixmap and display, keeping aspect ratio
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)
        self.video_label.setPixmap(pixmap.scaled(
            self.video_label.width(), self.video_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio
        ))

        # Update UI stats
        self.lbl_in.setText(f"People Entered: {self.count_in}")
        self.lbl_out.setText(f"People Exited: {self.count_out}")
        self.lbl_inside.setText(f"Currently Inside: {self.current_inside}")
        self.lbl_tracks.setText(f"Active Tracks: {self.active_tracks}")
        self.lbl_status.setText("Status: OVER CAPACITY!" if self.over_capacity else "Status: Normal")
        self.lbl_status.setStyleSheet("color: red;" if self.over_capacity else "color: green;")

        # Session time
        if self.session_start_time:
            elapsed = int(time.time() - self.session_start_time)
            h_, rem = divmod(elapsed, 3600)
            m_, s_ = divmod(rem, 60)
            self.lbl_session.setText(f"Session Time: {h_:02d}:{m_:02d}:{s_:02d}")

        # Auto-save
        if self.settings.get('auto_save', True) and time.time() - self.last_save > self.settings.get('save_interval', 60):
            self.save_session_data()
            self.last_save = time.time()

    # ---------------- Data / Export / Reset ----------------
    def reset_counts(self):
        reply = QMessageBox.question(
            self, "Confirm Reset",
            "Are you sure you want to reset all counts?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.counter:
                self.counter.reset_counts()
            self.count_in = self.count_out = self.current_inside = self.active_tracks = 0
            self.lbl_in.setText("People Entered: 0")
            self.lbl_out.setText("People Exited: 0")
            self.lbl_inside.setText("Currently Inside: 0")
            self.lbl_tracks.setText("Active Tracks: 0")
            self.lbl_status.setText("Status: Normal")
            self.lbl_status.setStyleSheet("color: green;")
            QMessageBox.information(self, "Reset", "All counts have been reset.")

    def export_data(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Data", "", "JSON Files (*.json);;Text Files (*.txt)"
        )
        if not filename:
            return

        data = {
            'timestamp': datetime.now().isoformat(),
            'session_data': {
                'count_in': self.count_in,
                'count_out': self.count_out,
                'current_inside': self.current_inside,
                'session_duration': self.lbl_session.text().replace("Session Time: ", "")
            },
            'settings': self.settings
        }

        try:
            if filename.lower().endswith(".json"):
                with open(filename, "w") as f:
                    json.dump(data, f, indent=4)  # pretty JSON
            else:  # Save as human-readable TXT
                with open(filename, "w") as f:
                    f.write("=== People Counter Report ===\n")
                    f.write(f"Timestamp: {data['timestamp']}\n")
                    f.write(f"People Entered: {data['session_data']['count_in']}\n")
                    f.write(f"People Exited: {data['session_data']['count_out']}\n")
                    f.write(f"Currently Inside: {data['session_data']['current_inside']}\n")
                    f.write(f"Session Duration: {data['session_data']['session_duration']}\n")
                    f.write("\n--- Settings ---\n")
                    for k, v in data['settings'].items():
                        f.write(f"{k}: {v}\n")

            QMessageBox.information(self, "Export", f"Data exported to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def save_session_data(self):
        try:
            if not os.path.exists('sessions'):
                os.makedirs('sessions')
            filename = f"sessions/session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            data = {
                'timestamp': datetime.now().isoformat(),
                'count_in': self.count_in,
                'count_out': self.count_out,
                'current_inside': self.current_inside
            }
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print("Auto-save error:", e)

    # ---------------- Settings persistence ----------------
    def load_settings(self):
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
        except Exception as e:
            print("Failed to load settings:", e)

    def save_settings(self):
        try:
            with open('settings.json', 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print("Failed to save settings:", e)

    def import_settings(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Import Settings", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'r') as f:
                    new_settings = json.load(f)
                # support both raw settings or wrapped dict
                if 'settings' in new_settings:
                    new_settings = new_settings['settings']
                self.settings.update(new_settings)
                self.apply_settings_to_ui()
                self.save_settings()
                QMessageBox.information(self, "Import", "Settings imported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", str(e))

    def export_settings(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Export Settings", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump({'settings': self.settings}, f, indent=2)
                QMessageBox.information(self, "Export", f"Settings exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def apply_settings_to_ui(self):
        # Apply stored settings to UI controls
        self.capacity_spin.setValue(self.settings.get('max_capacity', 10))
        self.line_slider.setValue(self.settings.get('line_position', 240))
        self.direction_combo.setCurrentText(self.settings.get('direction', 'horizontal'))
        self.conf_slider.setValue(int(self.settings.get('confidence', 0.4) * 10))
        self.save_interval_spin.setValue(self.settings.get('save_interval', 60))
        theme = self.settings.get('theme', 'Dark')
        self.theme_combo.setCurrentText(theme)
        self.change_theme(theme)

    # ---------------- About & Closing ----------------
    def show_about(self):
        QMessageBox.information(self, "About", """
Real-Time People Counter & Tracker
Version 1.0

Features:
• Real-time person detection (YOLO or custom)
• Multi-object tracking
• Configurable counting line
• Capacity monitoring
• Data export functionality (JSON / TXT)
• Auto-save sessions

Created for professional people counting applications.
""")

    def closeEvent(self, event):
        # Ensure graceful shutdown
        if self.is_running:
            self.stop_counting()
        try:
            self.save_session_data()
        except:
            pass
        self.save_settings()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Splash screen
    splash_pix = QPixmap(400, 300)
    splash_pix.fill(Qt.GlobalColor.white)
    splash = QSplashScreen(splash_pix)
    splash.showMessage("Loading People Counter...", Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.black)
    splash.show()
    app.processEvents()

    # Load main window
    win = PeopleCounterApp()
    time.sleep(1)  # simulate load delay (can remove or adjust)
    win.show()
    splash.finish(win)

    sys.exit(app.exec())

