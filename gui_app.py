import sys
import cv2
import json
import os
import time
import math
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QSpinBox, QSlider, QComboBox, QGroupBox, QFileDialog,
    QMessageBox, QStatusBar, QMenuBar, QMenu, QStyle, QSplashScreen,
    QProgressBar, QDialog
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QRect
from PyQt6.QtGui import QImage, QPixmap, QAction, QPainter, QFont, QBrush, QLinearGradient, QColor

# Global variables to store imported modules
detector_module = None
tracker_module = None
counter_module = None
visualizer_module = None

def load_modules():
    """Load AI modules with error handling"""
    global detector_module, tracker_module, counter_module, visualizer_module
    
    print("Loading modules...")
    
    try:
        import detector
        detector_module = detector
        print("✓ Detector module loaded")
    except ImportError as e:
        print(f"✗ Detector module not found: {e}")
    except Exception as e:
        print(f"✗ Error loading detector: {e}")
    
    try:
        import tracker
        tracker_module = tracker
        print("✓ Tracker module loaded")
    except ImportError as e:
        print(f"✗ Tracker module not found: {e}")
    except Exception as e:
        print(f"✗ Error loading tracker: {e}")
    
    try:
        import counter
        counter_module = counter
        print("✓ Counter module loaded")
    except ImportError as e:
        print(f"✗ Counter module not found: {e}")
    except Exception as e:
        print(f"✗ Error loading counter: {e}")
    
    try:
        import visualizer
        visualizer_module = visualizer
        print("✓ Visualizer module loaded")
    except ImportError as e:
        print(f"✗ Visualizer module not found: {e}")
    except Exception as e:
        print(f"✗ Error loading visualizer: {e}")

class EnhancedSplashScreen(QSplashScreen):
    """Enhanced attractive splash screen"""
    def __init__(self):
        # Smaller, wide splash (500x200)
        pixmap = QPixmap(500, 200)

        super().__init__(pixmap)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        self.background = QPixmap("human-eye.jpg")

        # Progress tracking
        self.progress = 0
        self.message = "Loading..."

        # Animation timer for smooth effects
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(30)  # Update every 30ms
        self.animation_step = 0

    def update_progress(self, progress, message=""):
        self.progress = progress
        if message:
            self.message = message
        self.repaint()
        QApplication.processEvents()

    def update_animation(self):
        self.animation_step += 1
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # ✅ Draw background image
        if hasattr(self, "background") and not self.background.isNull():
            painter.drawPixmap(self.rect(), self.background)
        else:
            # fallback gradient if no image
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0, QColor(52, 73, 94))
            gradient.setColorAt(1, QColor(36, 52, 66))
            painter.fillRect(self.rect(), QBrush(gradient))

        # ✅ Dark overlay for better contrast
        overlay = QColor(0, 0, 0, 120)  # black with 120 alpha
        painter.fillRect(self.rect(), overlay)

        # Title
        title_rect = QRect(0, 30, self.width(), 40)
        title_text = "People Counter & Tracker"

        # Shadow for title
        painter.setPen(QColor(0, 0, 0, 200))
        painter.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        painter.drawText(title_rect.adjusted(2, 2, 2, 2),
                        Qt.AlignmentFlag.AlignCenter, title_text)

        # Main title
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, title_text)

        # Subtitle
        subtitle_rect = QRect(0, 65, self.width(), 20)
        subtitle_text = "Real-Time Detection"

        # Shadow for subtitle
        painter.setPen(QColor(0, 0, 0, 180))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(subtitle_rect.adjusted(1, 1, 1, 1),
                        Qt.AlignmentFlag.AlignCenter, subtitle_text)

        # Main subtitle
        painter.setPen(QColor(225, 225, 225))
        painter.drawText(subtitle_rect, Qt.AlignmentFlag.AlignCenter, subtitle_text)

        # Animated loading text
        dots = "." * ((self.animation_step // 8) % 4)
        loading_text = f"{self.message}{dots}"
        painter.setFont(QFont("Arial", 9))

        # Shadow for loading text
        painter.setPen(QColor(0, 0, 0, 200))
        painter.drawText(32, self.height() - 58, loading_text)

        # Main loading text
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(30, self.height() - 60, loading_text)

        # Progress bar
        bar_width = self.width() - 60
        bar_height = 12
        bar_x = 30
        bar_y = self.height() - 35

        bg_rect = QRect(bar_x, bar_y, bar_width, bar_height)
        painter.setBrush(QBrush(QColor(34, 49, 63, 200)))  # semi-transparent bg
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(bg_rect, 6, 6)

        # Border
        painter.setPen(QColor(52, 152, 219, 150))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(bg_rect, 6, 6)

        # Progress fill
        if self.progress > 0:
            fill_width = int(bar_width * self.progress / 100)
            fill_rect = QRect(bar_x, bar_y, fill_width, bar_height)

            progress_gradient = QLinearGradient(bar_x, bar_y, bar_x, bar_y + bar_height)
            progress_gradient.setColorAt(0, QColor(52, 152, 219))
            progress_gradient.setColorAt(1, QColor(41, 128, 185))

            painter.setBrush(QBrush(progress_gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(fill_rect, 6, 6)

        # Percentage text with shadow
        percent_text = f"{self.progress}%"
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))

        painter.setPen(QColor(0, 0, 0, 200))
        painter.drawText(bg_rect.adjusted(1, 1, 1, 1),
                        Qt.AlignmentFlag.AlignCenter, percent_text)

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(bg_rect, Qt.AlignmentFlag.AlignCenter, percent_text)



class CameraLoadingDialog(QDialog):
    """Enhanced camera loading dialog with attractive animations"""
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.settings = settings or {}
        self.setWindowTitle("Camera Initialization")
        self.setFixedSize(450, 280)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Icon/Logo area with animated circle
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(80, 80)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("""
            QLabel {
                background-color: #3498db;
                border-radius: 40px;
                color: white;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        self.icon_label.setText("📹")
        
        # Center the icon
        icon_layout = QHBoxLayout()
        icon_layout.addStretch()
        icon_layout.addWidget(self.icon_label)
        icon_layout.addStretch()
        layout.addLayout(icon_layout)
        
        # Title
        title = QLabel("Initializing Camera System")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            color: white; 
        """)
        layout.addWidget(title)
        
        # Status label
        self.status_label = QLabel("Connecting to camera...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            font-size: 13px; 
            color: #bdc3c7; 
            margin: 5px;
        """)
        layout.addWidget(self.status_label)
        
        # Enhanced progress bar - FIXED: Changed from self.progress_bar to self.progressBar
        self.progressBar = QProgressBar()  # Changed attribute name to match the update_progress method
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)
        self.progressBar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #34495e;
                border-radius: 12px;
                background-color: #2c3e50;
                color: white;
                text-align: center;
                font-weight: bold;
                font-size: 12px;
                min-height: 20px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 10px;
                margin: 2px;
            }
        """)
        layout.addWidget(self.progressBar)
        
        # Animated elements container
        animation_layout = QHBoxLayout()
        animation_layout.setSpacing(10)
        
        # Create animated dots
        self.dots = []
        for i in range(5):
            dot = QLabel("●")
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dot.setStyleSheet("""
                font-size: 16px; 
                color: #3498db; 
                margin: 5px;
            """)
            self.dots.append(dot)
            animation_layout.addWidget(dot)
        
        # Center the dots
        dots_container = QHBoxLayout()
        dots_container.addStretch()
        dots_container.addLayout(animation_layout)
        dots_container.addStretch()
        layout.addLayout(dots_container)
        
        self.setLayout(layout)
        
        # Animation timers
        self.dot_timer = QTimer()
        self.dot_timer.timeout.connect(self.animate_dots)
        self.dot_timer.start(200)
        self.dot_index = 0
        
        self.icon_timer = QTimer()
        self.icon_timer.timeout.connect(self.animate_icon)
        self.icon_timer.start(100)
        self.icon_scale = 0
        
        # Apply dark theme with gradient
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34495e, stop:1 #2c3e50);
                border-radius: 15px;
                border: 2px solid #3498db;
            }
        """)
        
    def animate_dots(self):
        """Animate the loading dots"""
        # Reset all dots
        for dot in self.dots:
            dot.setStyleSheet("""
                font-size: 16px; 
                color: #555; 
                margin: 5px;
            """)
        
        # Highlight current dot
        if self.dots:
            self.dots[self.dot_index].setStyleSheet("""
                font-size: 18px; 
                color: #3498db; 
                margin: 5px;
                font-weight: bold;
            """)
        
        self.dot_index = (self.dot_index + 1) % len(self.dots)
        
    def animate_icon(self):
        """Animate the camera icon with pulsing effect"""
        scale_factor = 1.0 + 0.1 * math.sin(self.icon_scale * 0.2)
        self.icon_scale += 1
        
        # Create pulsing effect
        alpha = int(150 + 105 * math.sin(self.icon_scale * 0.15))
        self.icon_label.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(52, 152, 219, {alpha});
                border-radius: 40px;
                color: white;
                font-size: {int(24 * scale_factor)}px;
                font-weight: bold;
                border: 3px solid rgba(52, 152, 219, 100);
            }}
        """)
        
    def update_progress(self, value, message=""):
        """Update progress bar and status message"""
        self.progressBar.setValue(value)  # Fixed: Changed from progress_bar to progressBar
        if message:
            self.status_label.setText(message)
        QApplication.processEvents()
        
    def closeEvent(self, event):
        """Clean up timers when closing"""
        self.dot_timer.stop()
        self.icon_timer.stop()
        super().closeEvent(event)

class CameraInitWorker(QThread):
    """Simplified camera initialization worker"""
    camera_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    progress_updated = pyqtSignal(int, str)
    
    def __init__(self, camera_index, settings):
        super().__init__()
        self.camera_index = camera_index
        self.settings = settings

    def run(self):
        global detector_module, tracker_module, counter_module, visualizer_module
        try:
            # Open camera
            cap = cv2.VideoCapture(self.camera_index)
            
            if not cap.isOpened():
                self.error_occurred.emit("Could not open camera")
                return
                
            # Configure camera
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # Initialize AI components if available
            detector = None
            tracker = None
            counter = None
            visualizer = None
            
            if detector_module:
                try:
                    detector = detector_module.PersonDetector(confidence=self.settings['confidence'])
                except Exception as e:
                    print(f"Error creating detector: {e}")
            
            if tracker_module:
                try:
                    tracker = tracker_module.MultiObjectTracker()
                except Exception as e:
                    print(f"Error creating tracker: {e}")
            
            if counter_module:
                try:
                    counter = counter_module.PeopleCounter(
                        line_position=self.settings['line_position'],
                        direction=self.settings['direction'],
                        max_capacity=self.settings['max_capacity']
                    )
                except Exception as e:
                    print(f"Error creating counter: {e}")
            
            if visualizer_module:
                try:
                    visualizer = visualizer_module.Visualizer(
                        line_position=self.settings['line_position'],
                        direction=self.settings['direction']
                    )
                except Exception as e:
                    print(f"Error creating visualizer: {e}")
            
            # Package everything
            camera_package = {
                'cap': cap,
                'detector': detector,
                'tracker': tracker,
                'counter': counter,
                'visualizer': visualizer
            }
            
            self.camera_ready.emit(camera_package)
            
        except Exception as e:
            self.error_occurred.emit(f"Camera initialization failed: {str(e)}")

class PeopleCounterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        print("Initializing PeopleCounterApp...")

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
            QComboBox, QSlider {
                background-color: #34495e;
                color: white;
                border-radius: 4px;
                padding: 4px;
            }

            QSpinBox {
                background-color: #34495e;
                color: white;
                border: 1px solid #2c3e50;
                border-radius: 4px;
                padding-right: 15px; /* make space for the buttons */
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
            QComboBox, QSlider {
                background-color: #ffffff;
                color: black;
                border-radius: 4px;
                padding: 4px;
            }

            QSpinBox {
                background-color: #34495e;
                color: white;
                border: 1px solid #2c3e50;
                border-radius: 4px;
                padding-right: 15px; /* make space for the buttons */
            }

            QStatusBar { background-color: #bdc3c7; color: black; }
        """

        # Initialize UI
        self.init_ui()

        # Track stats
        self.count_in = 0
        self.count_out = 0
        self.current_inside = 0
        self.active_tracks = 0
        self.over_capacity = False

        # Apply saved theme
        self.change_theme(self.settings.get("theme", "Dark"))
        
        print("PeopleCounterApp initialized successfully!")

    def init_ui(self):
        """Initialize the user interface"""
        print("Setting up UI...")
        
        # Central widget and layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # --- Video feed panel ---
        self.video_label = QLabel("Camera Feed Will Appear Here\nClick 'Start Counting'")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; color: white; font-size: 14px;")
        self.video_label.setMinimumSize(640, 480)
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
        
        # Check module availability
        modules_available = sum([
            detector_module is not None,
            tracker_module is not None,
            counter_module is not None,
            visualizer_module is not None
        ])
        
        if modules_available == 4:
            self.status.showMessage("Ready - All AI modules loaded")
        elif modules_available > 0:
            self.status.showMessage(f"Ready - {modules_available}/4 AI modules loaded (limited functionality)")
        else:
            self.status.showMessage("Ready - No AI modules loaded (camera only)")

        # Menu bar
        self.create_menu()

        # Timer for video updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        
        print("UI setup complete!")

    def create_settings_group(self):
        group = QGroupBox("Settings")
        vbox = QVBoxLayout(group)

        # Max capacity
        self.capacity_spin = QSpinBox()
        self.capacity_spin.setRange(1, 1000)
        self.capacity_spin.setValue(self.settings['max_capacity'])
        self.capacity_spin.valueChanged.connect(self.update_max_capacity)
        self.capacity_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
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

        # Start/Stop button
        self.start_button = QPushButton(" Start Counting")
        self.start_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.start_button.setToolTip("Start people counting")
        self.start_button.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        self.start_button.clicked.connect(self.toggle_counting)
        vbox.addWidget(self.start_button)

        # Reset button
        self.reset_button = QPushButton(" Reset Counts")
        self.reset_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.reset_button.setToolTip("Reset all counts")
        self.reset_button.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold;")
        self.reset_button.clicked.connect(self.reset_counts)
        vbox.addWidget(self.reset_button)

        # Export button
        self.export_button = QPushButton(" Export Data")
        self.export_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.export_button.setToolTip("Export session data")
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

    def change_theme(self, theme_name):
        if theme_name == "Dark":
            self.setStyleSheet(self.dark_theme)
            self.settings["theme"] = "Dark"
        else:
            self.setStyleSheet(self.light_theme)
            self.settings["theme"] = "Light"
        self.save_settings()

    # ---------------- Camera and Counting Logic ----------------
    def toggle_counting(self):
        if not self.is_running:
            self.start_counting()
        else:
            self.stop_counting()

    def start_counting(self):
        """Start counting with enhanced camera loading dialog"""
        print("Starting counting...")
    
        # Show attractive camera loading dialog
        self.camera_loading_dialog = CameraLoadingDialog(self, self.settings)
        self.camera_loading_dialog.show()
        
        # Disable start button during initialization
        self.start_button.setEnabled(False)
        self.status.showMessage("Initializing camera system...")
        
        # Start camera initialization in background
        self.camera_worker = CameraInitWorker(self.settings['camera_index'], self.settings)
        self.camera_worker.progress_updated.connect(self.camera_loading_dialog.update_progress)
        self.camera_worker.camera_ready.connect(self.on_camera_ready)
        self.camera_worker.error_occurred.connect(self.on_camera_error)
        self.camera_worker.start()

    def on_camera_ready(self, camera_package):
        """Called when camera and AI components are ready"""
        print("Camera ready!")
        
        # Close loading dialog with a slight delay for smooth UX
        if self.camera_loading_dialog:
            # Show completion message briefly
            self.camera_loading_dialog.update_progress(100, "Launching camera feed...")
            QApplication.processEvents()
            time.sleep(0.3)
            self.camera_loading_dialog.close()
            self.camera_loading_dialog = None
        
        # Set up components
        self.cap = camera_package['cap']
        self.detector = camera_package['detector']
        self.tracker = camera_package['tracker']
        self.counter = camera_package['counter']
        self.visualizer = camera_package['visualizer']
        
        # Start the session
        self.session_start_time = time.time()
        self.is_running = True
        
        # Update UI
        self.start_button.setText(" Stop Counting")
        self.start_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.start_button.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold;")
        self.start_button.setEnabled(True)
        
        # Check if AI modules are available
        ai_available = all([self.detector, self.tracker, self.counter, self.visualizer])
        if ai_available:
            self.status.showMessage("🟢 Counting active - All AI features operational")
        else:
            missing = []
            if not self.detector: missing.append("detector")
            if not self.tracker: missing.append("tracker")
            if not self.counter: missing.append("counter")
            if not self.visualizer: missing.append("visualizer")
            self.status.showMessage(f"🟡 Counting active - Missing: {', '.join(missing)}")
        
        # Start video timer
        self.timer.start(30)  # 30ms = ~33 FPS

    def on_camera_error(self, error_message):
        """Called when camera initialization fails"""
        print(f"Camera error: {error_message}")
        
        # Close loading dialog
        if self.camera_loading_dialog:
            self.camera_loading_dialog.close()
            self.camera_loading_dialog = None
        
        # Re-enable start button
        self.start_button.setEnabled(True)
        self.status.showMessage("❌ Camera initialization failed")
        
        # Show detailed error message
        QMessageBox.critical(self, "Camera Error", 
                           f"Failed to initialize camera:\n\n{error_message}\n\n"
                           "Possible solutions:\n"
                           "• Check if camera is connected\n"
                           "• Close other applications using the camera\n"
                           "• Try a different camera index in settings\n"
                           "• Restart the application")

    def stop_counting(self):
        print("Stopping counting...")
        
        self.is_running = False
        self.timer.stop()
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Reset UI
        self.start_button.setText(" Start Counting")
        self.start_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.start_button.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        self.status.showMessage("Stopped")
        self.video_label.setText("Camera Feed Stopped\nClick 'Start Counting'")

    def update_frame(self):
        if not self.cap or not self.is_running:
            return
            
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to read frame")
            return

        # Main AI pipeline - only if all modules are available
        if all([self.detector, self.tracker, self.counter]):
            try:
                detections = self.detector.detect(frame)
                tracked_objects = self.tracker.update(frame, detections)

                active_ids = [obj["id"] for obj in tracked_objects]
                for obj in tracked_objects:
                    self.counter.check_crossing(obj["id"], obj["bbox"])
                self.counter.cleanup_lost_tracks(active_ids)

                # Update stats
                self.count_in, self.count_out = self.counter.get_counts()
                self.over_capacity, self.current_inside = self.counter.is_over_capacity()
                self.active_tracks = len(tracked_objects)

                # Draw visualization
                if self.visualizer:
                    frame = self.visualizer.draw(frame, tracked_objects,
                                                 self.count_in, self.count_out,
                                                 self.over_capacity, self.current_inside)
            except Exception as e:
                print(f"Error in AI pipeline: {e}")
                # Continue with basic video display

        # Convert frame to Qt format and display
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_img)
            
            # Scale to fit label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.video_label.width(), self.video_label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.video_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"Error displaying frame: {e}")

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

    # ---------------- Data Management ----------------
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
            self.over_capacity = False
            
            # Update UI
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
                    json.dump(data, f, indent=4)
            else:  # Save as TXT
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

    # ---------------- Settings Management ----------------
    def load_settings(self):
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
                    print("Settings loaded successfully")
        except Exception as e:
            print(f"Failed to load settings: {e}")

    def save_settings(self):
        try:
            with open('settings.json', 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    # ---------------- About & Closing ----------------
    def show_about(self):
        QMessageBox.information(self, "About", """
Real-Time People Counter & Tracker
Version 2.0 Simplified

Features:
• Real-time person detection with AI (if modules available)
• Multi-object tracking
• Configurable counting parameters
• Data export functionality
• Dark/Light theme support
• Robust error handling

This version will work even if AI modules are missing.
Basic camera functionality is always available.

Created for professional people counting applications.
""")

    def closeEvent(self, event):
        print("Closing application...")
        if self.is_running:
            self.stop_counting()
        self.save_settings()
        event.accept()


def main():
    """Main application entry point with simplified splash screen"""
    print("Starting People Counter application...")
    
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("People Counter & Tracker")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("AI Vision Solutions")
    
    # Create and show enhanced splash screen
    splash = EnhancedSplashScreen()
    splash.show()
    
    # Load modules with attractive progress updates
    splash.update_progress(5, "Initializing application")
    QApplication.processEvents()
    time.sleep(0.3)
    
    splash.update_progress(15, "Loading AI modules")
    QApplication.processEvents()
    
    load_modules()
    
    splash.update_progress(50, "Setting up user interface")
    QApplication.processEvents()
    time.sleep(0.4)
    
    # Create main window
    splash.update_progress(75, "Configuring components")
    QApplication.processEvents()
    time.sleep(0.3)
    
    try:
        main_window = PeopleCounterApp()
        
        splash.update_progress(100, "Ready!")
        QApplication.processEvents()
        time.sleep(0.5)
        
        # Show main window and close splash
        main_window.show()
        splash.finish(main_window)
        
        print("Application started successfully!")
        
    except Exception as e:
        splash.close()
        print(f"Error starting application: {e}")
        QMessageBox.critical(None, "Startup Error", 
                           f"Failed to start application:\n{str(e)}\n\nCheck console for details.")
        return 1
    
    # Run application
    try:
        return app.exec()
    except Exception as e:
        print(f"Runtime error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())