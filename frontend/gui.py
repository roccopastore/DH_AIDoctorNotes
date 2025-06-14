import sys
import shutil
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QHBoxLayout,
    QVBoxLayout, QFrame, QTextEdit, QGraphicsDropShadowEffect, QSizePolicy,
    QLayout
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, pyqtSignal, QThread, QRect, QUrl
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QPixmap, QConicalGradient, QIcon, QMovie
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

import time
import os
from playwright.sync_api import sync_playwright
from urllib.request import pathname2url
from archivie_window import ArchivieWindow
from pathlib import Path

# Append backend path to system path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from handle_rec import start_recording
from backend_main import handle_output
from handle_video import info_video

# Global variables to store output and save time
output = []
save_time = 0

class WorkerThread(QThread):
    """
    A QThread that runs the backend processing in the background
    to avoid freezing the GUI.
    """
    finished = pyqtSignal()

    def run(self):
        """
        Executes the backend's handle_output function and emits a signal upon completion.
        """
        global output
        global save_time
        save_time = time.time()
        output = handle_output(save_time)
        self.finished.emit()


class RecordingButton(QPushButton):
    """
    A custom QPushButton that acts as a recording toggle,
    complete with animations and a spinning indicator.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recording = False
        self.spinner_angle = 0
        self.spinner_opacity = 0.0

        # Timer for the spinner animation
        self.spin_timer = QTimer(self)
        self.spin_timer.timeout.connect(self.rotate_spinner)

        # Animation for button size change
        self._size_anim = QPropertyAnimation(self, b"minimumSize")
        self._size_anim.setDuration(200)
        self._size_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.setFixedSize(80, 80)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(self.base_style())

        self.setIcon(QIcon("frontend/icons/mic_icon.png"))
        self.setIconSize(QSize(40, 40))

    def base_style(self):
        """Returns the base CSS style for the button."""
        return """
            QPushButton {
                background-color: #f0f8ff;
                border: 4px solid #bbdefb;
                border-radius: 40px;
                color: #0d47a1;
                font-size: 16px;
            }
            QPushButton:hover {
                border-color: #90caf9;
            }
            QPushButton:pressed {
                border-color: #64b5f6;
            }
        """

    def toggle_recording(self):
        """
        Toggles the recording state, changes the icon, and starts/stops animations.
        """
        self.recording = not self.recording
        if self.recording:
            self.setIcon(QIcon('frontend/icons/stop_icon.png'))
            self.setIconSize(QSize(40, 40))
            # Start size increase animation
            self._size_anim.stop()
            self._size_anim.setStartValue(self.size())
            self._size_anim.setEndValue(self.size() + QSize(10, 10))
            self._size_anim.start()
            self.spin_timer.start(16)  # Approx 60 FPS
            start_recording()

    def rotate_spinner(self):
        """Updates the spinner's angle and opacity for animation."""
        self.spinner_angle = (self.spinner_angle + 5) % 360
        if self.spinner_opacity < 1.0:
            self.spinner_opacity = min(1.0, self.spinner_opacity + 0.05)
        self.update() # Triggers a repaint

    def paintEvent(self, event):
        """
        Custom paint event to draw the spinning gradient border when recording.
        """
        super().paintEvent(event)
        if self.recording:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            gradient = QConicalGradient(self.rect().center(), self.spinner_angle)
            gradient.setColorAt(0.0, QColor(85, 214, 121, int(self.spinner_opacity * 255)))
            gradient.setColorAt(0.25, QColor(85, 214, 121, 0)) # Fades to transparent
            pen = QPen(QBrush(gradient), 6)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            radius = min(self.width(), self.height()) / 2 - 3
            painter.drawEllipse(self.rect().center(), int(radius), int(radius))


class Card(QFrame):
    """
    A custom QFrame that acts as a card to display either text or video content.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 20px;
            }
            QPushButton {
                background-color: #bbdefb;
                color: #0d47a1;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #90caf9;
            }
        """)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(20, 20, 20, 20)

        self.video_check = False

        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(10)
        self.content_layout.setAlignment(Qt.AlignCenter)

        # QTextEdit for displaying text content
        self.text_widget = QTextEdit()
        self.text_widget.setReadOnly(True)
        self.text_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.text_widget.setMinimumHeight(420)
        self.text_widget.setStyleSheet("""
            QTextEdit {
                color: black;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                background-color: white;
            }
        """)
        self.text_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_widget.hide()

        # QVideoWidget for displaying video content
        self.video_widget = QVideoWidget()
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_widget.setMinimumHeight(420)
        self.video_widget.hide()

        # Media Player for video playback
        self.media_player = QMediaPlayer(self)
        self.media_player.setVideoOutput(self.video_widget)

        # Video playback controls
        self.video_controls = QHBoxLayout()
        self.play_button = QPushButton()
        self.play_button.setIcon(QIcon('frontend/icons/play_icon.png'))
        self.play_button.setStyleSheet("background-color: transparent; border: none;")
        self.pause_button = QPushButton()
        self.pause_button.setIcon(QIcon('frontend/icons/pause_icon.png'))
        self.pause_button.setStyleSheet("background-color: transparent; border: none;")

        self.play_button.clicked.connect(self.media_player.play)
        self.pause_button.clicked.connect(self.media_player.pause)

        self.video_controls.addWidget(self.play_button)
        self.video_controls.addWidget(self.pause_button)

        self.content_layout.addWidget(self.text_widget)
        self.content_layout.addWidget(self.video_widget)
        self.content_layout.addLayout(self.video_controls)

        outer_layout.addLayout(self.content_layout)
        self.setFixedSize(400, 500)

        # Add a drop shadow for a modern look
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

    def show_text(self, html):
        """Configures the card to display HTML text."""
        self.video_widget.hide()
        self.play_button.hide()
        self.pause_button.hide()
        self.media_player.pause()

        self.text_widget.setHtml(html)
        self.text_widget.show()

    def show_video(self, path):
        """Configures the card to display video from a given path."""
        global save_time
        self.video_check = True

        # Check if the final "video.mp4" file exists.
        if os.path.exists(path + "/video.mp4"):
            self.video = QMediaContent(QUrl.fromLocalFile(os.path.abspath(path + "/video.mp4")))
        else:
            # If not, read the video ID and try to process it.
            with open(path + "/id.txt", "r", encoding="utf-8") as file:
                id = file.read().strip()
                check = info_video(id, save_time)
                print(check)
                # Load the final video if processing was successful, otherwise load the temporary one.
                if check:
                    self.video = QMediaContent(QUrl.fromLocalFile(os.path.abspath(path + "/video.mp4")))
                else:
                    self.video = QMediaContent(QUrl.fromLocalFile(os.path.abspath(path + "/videoT.mp4")))
        
        # Hide text widget and show video player and controls
        self.text_widget.hide()
        self.video_widget.show()
        self.play_button.show()
        self.pause_button.show()
        self.media_player.setMedia(self.video)
        self.media_player.setPosition(0) # Rewind to start


class MainWindow(QWidget):
    """The main application window."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AIDOCTORNOTES")
        self.setFixedSize(600, 750)
        self.setStyleSheet("background-color: #f0f8ff;")
        self.current_card_index = 1 # Start with the "CONVERSATION" card
        self.card_data = [
            ("Avatar Simulation", "Animated video simulation of the conversation..."),
            ("Transcription", "Transcribed text of the conversation..."),
            ("Summary", "Summary of the conversation between patient and doctor...")
        ]
        self.setup_ui()

    def setup_ui(self):
        """Initializes and lays out all UI components."""
        self.main_layout = QVBoxLayout(self)
        self.nav_labels = ["VIDEO", "CONVERSATION", "DOCTOR'S NOTES"]

        # Transparent overlay for the loading animation
        self.overlay = QWidget(self)
        self.overlay.setGeometry(self.rect())
        self.overlay.setWindowOpacity(0.4)
        self.overlay.hide()

        # Centered GIF label in the overlay
        self.movie = QMovie("./frontend/animations/loading.gif")
        if not self.movie.isValid():
            print("GIF is not valid or not found")
        self.movie_label = QLabel(self.overlay)
        self.movie_label.setMovie(self.movie)
        self.movie_label.setAlignment(Qt.AlignCenter)
        self.movie_label.setScaledContents(False)
        self.movie_label.setFixedSize(500, 500)

        # Center the GIF within the overlay
        overlay_layout = QVBoxLayout(self.overlay)
        overlay_layout.setAlignment(Qt.AlignCenter)
        overlay_layout.addWidget(self.movie_label)
        self.overlay.setLayout(overlay_layout)

        # Top bar with logo and archive button
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        logo = QLabel()
        logo.setPixmap(QPixmap('frontend/icons/logo.png').scaled(250, 250, Qt.KeepAspectRatio))
        self.archivie_button = QPushButton()
        self.archivie_button.setCursor(Qt.PointingHandCursor)
        self.archivie_button.setStyleSheet("background-color: transparent; border: none;")
        self.archivie_button.setIcon(QIcon("frontend/icons/archivie_icon.png"))
        self.archivie_button.setIconSize(QSize(30, 30))
        self.archivie_button.clicked.connect(self.show_archivie)
        top_bar.addWidget(logo, alignment=Qt.AlignLeft)
        top_bar.addWidget(self.archivie_button, alignment=Qt.AlignRight)

        # Main action buttons
        self.record_button = RecordingButton()
        self.record_button.clicked.connect(self.toggle_recording)
        self.download_button = QPushButton()
        self.download_button.setFixedSize(80, 80)
        self.download_button.setCursor(Qt.PointingHandCursor)
        self.download_button.setIcon(QIcon('frontend/icons/download_icon.png'))
        self.download_button.setIconSize(QSize(40, 40))
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f8ff;
                border: 4px solid #bbdefb;
                border-radius: 40px;
                color: #0d47a1;
                font-size: 16px;
            }
            QPushButton:hover {
                border-color: #90caf9;
            }
            QPushButton:pressed {
                border-color: #64b5f6;
            }""")
        self.download_button.hide()

        # The main content card
        self.card = Card()
        self.card.hide()

        # Bottom navigation controls (arrows, labels, dots)
        navigation = QHBoxLayout()
        navigation_left = QVBoxLayout()
        navigation_right = QVBoxLayout()
        
        self.prev_text = QLabel(self.nav_labels[0])
        self.prev_text.setAlignment(Qt.AlignCenter)
        self.prev_text.setStyleSheet("font-size: 10px; color: #0d47a1; font-weight: bold")
        self.prev_text.setFixedWidth(100) 
        self.prev_text.hide()
        self.prev_btn = QPushButton()
        self.prev_btn.setIcon(QIcon('frontend/icons/left_arrow.png'))
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.setStyleSheet("background-color: transparent; border: none;")
        self.prev_btn.clicked.connect(self.prev_card)
        self.prev_btn.hide()
        navigation_left.addWidget(self.prev_text)
        navigation_left.addWidget(self.prev_btn)

        self.next_text = QLabel(self.nav_labels[2])
        self.next_text.setAlignment(Qt.AlignCenter)
        self.next_text.setStyleSheet("font-size: 10px; color: #0d47a1; font-weight: bold")
        self.next_text.setFixedWidth(100) 
        self.next_text.hide()
        self.next_btn = QPushButton()
        self.next_btn.setIcon(QIcon('frontend/icons/right_arrow.png'))
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setStyleSheet("background-color: transparent; border: none;")
        self.next_btn.clicked.connect(self.next_card)
        self.next_btn.hide()
        navigation_right.addWidget(self.next_text)
        navigation_right.addWidget(self.next_btn)

        navigation.addLayout(navigation_left)
        navigation.addStretch()
        self.dots = []
        for _ in self.card_data:
            dot = QLabel("●")
            dot.setStyleSheet("color: lightgray; font-size: 20px;")
            self.dots.append(dot)
            navigation.addWidget(dot, alignment=Qt.AlignCenter)
        navigation.addStretch()
        navigation.addLayout(navigation_right)

        # Assemble the main layout
        self.main_layout.addLayout(top_bar)
        self.main_layout.addStretch()
        center_layout = QHBoxLayout()
        center_layout.addWidget(self.record_button)
        center_layout.addWidget(self.download_button)
        self.main_layout.addLayout(center_layout)
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.card, alignment=Qt.AlignCenter)
        self.main_layout.addLayout(navigation)

        self.setLayout(self.main_layout)

    def show_archivie(self):
        """Shows the archive window and hides the main window."""
        current_pos = self.pos()
        self.archivie_window = ArchivieWindow(self)
        self.archivie_window.move(current_pos)
        self.archivie_window.show()
        self.hide()

    def toggle_recording(self):
        """Handles the logic when the recording button is clicked."""
        self.record_button.toggle_recording()
        if self.record_button.recording:
            # Hide elements not needed during recording
            self.card.hide()
            self.download_button.hide()
            self.archivie_button.setDisabled(True)
        else:
            # Stop recording and start processing
            self.record_button.setEnabled(False)
            self.archivie_button.setDisabled(False)

            # Show loading animation
            self.overlay.show()
            self.overlay.raise_()
            self.movie.start()

            # Start the backend processing in a separate thread
            self.thread = WorkerThread()
            self.thread.finished.connect(self.process_finished)
            self.thread.start()

    def process_finished(self):
            """Called when the worker thread is done processing."""
            # Re-enable and reset the record button
            self.record_button.setEnabled(True)
            self.record_button.setIcon(QIcon('frontend/icons/mic_icon.png'))
            self.record_button.setIconSize(QSize(40, 40))
            self.record_button._size_anim.stop()
            self.record_button._size_anim.setStartValue(self.size())
            self.record_button._size_anim.setEndValue(QSize(80, 80))
            self.record_button._size_anim.start()
            self.record_button.spin_timer.stop()

            # Hide loading animation
            self.movie.stop()
            self.overlay.hide()

            # Reset spinner state and show the results
            self.spinner_opacity = 0.0
            self.spinner_angle = 0
            self.show_card()
            self.next_btn.show()
            self.prev_btn.show()
            self.next_text.show()
            self.prev_text.show()
            self.download_button.show()
            
            # Connect the download button to the download function with correct paths
            global save_time
            folder_path = f"./backend/output/saves/{save_time}"
            self.download_button.clicked.connect(lambda _, c=folder_path + "/conversation.txt", v=folder_path + "/video.mp4", v2=folder_path + "/videoT.mp4", n=folder_path + "/notes.txt", f=save_time: self.download_files(c,v,v2,n,f))

    def show_card(self):
        """Displays the content for the currently selected card."""
        global output
        if self.current_card_index == 1:
            self.card.show_text(output[1]) # Conversation
        elif self.current_card_index == 0:
            self.card.show_video(output[0]) # Video
        elif self.current_card_index == 2:
            self.card.show_text(output[2]) # Doctor's Notes
        self.update_dots()
        self.update_nav()
        self.card.show()

    def update_nav(self):
        """Updates the navigation labels and button states."""
        if self.current_card_index == 0: # First card
            self.prev_btn.setDisabled(True)
            self.prev_text.setText("")
            self.next_text.setText(self.nav_labels[1])
        elif self.current_card_index == 2: # Last card
            self.next_btn.setDisabled(True)
            self.next_text.setText("")
            self.prev_text.setText(self.nav_labels[1])
        else: # Middle card
            self.prev_btn.setDisabled(False)
            self.prev_text.show()
            self.next_btn.setDisabled(False)
            self.next_text.show()
            self.prev_text.setText(self.nav_labels[0])
            self.next_text.setText(self.nav_labels[2])

    def update_dots(self):
        """Updates the navigation dots to highlight the current card."""
        for i, dot in enumerate(self.dots):
            if i == self.current_card_index:
                dot.setStyleSheet("color: #bbdefb; font-size: 20px;") # Active color
            else:
                dot.setStyleSheet("color: lightgray; font-size: 20px;") # Inactive color

    def next_card(self):
        """Switches to the next card."""
        if self.current_card_index < len(self.card_data) - 1:
            self.current_card_index += 1
            self.show_card()

    def prev_card(self):
        """Switches to the previous card."""
        if self.current_card_index > 0:
            self.current_card_index -= 1
            self.show_card()

    def download_files(self, conversation_path, video_path, video_path_2, notes_path, file_name):
        """
        Downloads the generated files (PDFs of notes/conversation and videos).
        """
        temp_notes_text = ""
        temp_notes_path = "./temp_files/temp_notes.html"
        temp_conversation_text = ""
        temp_conversation_path = "./temp_files/temp_conversation.html"

        # Read content from the original text files
        with open(notes_path, "r") as f:
            temp_notes_text = f.read()

        with open(temp_conversation_path, "w", encoding="utf-8") as f:
            f.write(temp_notes_text)

        with open(conversation_path, "r") as f:
            temp_conversation_text = f.read()
        
        with open(temp_conversation_path, "w", encoding="utf-8") as f:
            f.write(temp_conversation_text)
        
        # Define the save folder in the user's Downloads directory
        downloads_folder = Path.home() / "Downloads"
        save_folder = downloads_folder / f"AINotes_{file_name}"
        os.makedirs(save_folder, exist_ok=True)

        # Use Playwright to convert HTML content to PDF
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            # Convert notes to PDF
            page.goto('file://' + pathname2url(os.path.abspath(temp_notes_path)))
            pdf_path = save_folder / "notes.pdf"
            page.pdf(path=str(pdf_path), format="A4")
            # Convert conversation to PDF
            page.goto('file://' + pathname2url(os.path.abspath(temp_conversation_path)))
            pdf_path = save_folder / "conversation.pdf"
            page.pdf(path=str(pdf_path), format="A4")
            browser.close()
        
        # Copy video files to the save folder
        download_video2_path = save_folder / "videoT.mp4"
        shutil.copy(video_path_2, download_video2_path)

        if os.path.exists(video_path):
            download_video_path = save_folder / "video.mp4"
            shutil.copy(video_path, download_video_path)


if __name__ == "__main__":
    # Application entry point
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())