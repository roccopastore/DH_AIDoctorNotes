import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QHBoxLayout,
    QVBoxLayout, QFrame, QTextEdit, QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QPixmap, QConicalGradient, QIcon
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtMultimedia import QMediaPlayer
from handle_output import get_output
import time 
import os
from playwright.sync_api import sync_playwright
from urllib.request import pathname2url

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from handle_rec import start_recording
from backend_main import handle_output

output = []


class RecordingButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recording = False
        self.spinner_angle = 0
        self.spinner_opacity = 0.0

        self.spin_timer = QTimer(self)
        self.spin_timer.timeout.connect(self.rotate_spinner)

        self._size_anim = QPropertyAnimation(self, b"minimumSize")
        self._size_anim.setDuration(200)
        self._size_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.setFixedSize(80, 80)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(self.base_style())

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 50))
        self.setGraphicsEffect(shadow)

        self.setIcon(QIcon("frontend/icons/mic_icon.png"))
        self.setIconSize(QSize(40, 40))

    def base_style(self):
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
        self.recording = not self.recording
        if self.recording:
            self.setIcon(QIcon('frontend/icons/stop_icon.png'))
            self.setIconSize(QSize(40, 40))
            self._size_anim.stop()
            self._size_anim.setStartValue(self.size())
            self._size_anim.setEndValue(self.size() + QSize(10, 10))
            self._size_anim.start()
            self.spin_timer.start(16)
            start_recording()
        else:
            self.setIcon(QIcon('frontend/icons/mic_icon.png'))
            self.setIconSize(QSize(40, 40))
            self._size_anim.stop()
            self._size_anim.setStartValue(self.size())
            self._size_anim.setEndValue(QSize(80, 80))
            self._size_anim.start()
            self.spin_timer.stop()
            self.spinner_opacity = 0.0
            self.spinner_angle = 0
            self.update()
            global output
            output = handle_output(time.time())
            

    def rotate_spinner(self):
        self.spinner_angle = (self.spinner_angle + 5) % 360
        if self.spinner_opacity < 1.0:
            self.spinner_opacity = min(1.0, self.spinner_opacity + 0.05)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.recording:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            gradient = QConicalGradient(self.rect().center(), self.spinner_angle)
            gradient.setColorAt(0.0, QColor(85, 214, 121, int(self.spinner_opacity * 255)))
            gradient.setColorAt(0.25, QColor(85, 214, 121, 0))
            pen = QPen(QBrush(gradient), 6)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            radius = min(self.width(), self.height()) / 2 - 3
            painter.drawEllipse(self.rect().center(), int(radius), int(radius))


class Card(QFrame):
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

        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(10)
        self.content_layout.setAlignment(Qt.AlignCenter)

        # QTextEdit
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

        # QVideoWidget
        self.video_widget = QVideoWidget()
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_widget.setMinimumHeight(420)
        self.video_widget.hide()

        # Media Player
        self.media_player = QMediaPlayer(self)
        self.media_player.setVideoOutput(self.video_widget)

        # Video controls
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

        # Contenuto
        self.content_layout.addWidget(self.text_widget)
        self.content_layout.addWidget(self.video_widget)
        self.content_layout.addLayout(self.video_controls)

        outer_layout.addLayout(self.content_layout)
        self.setFixedSize(400, 500)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

    def show_text(self, html):
        self.video_widget.hide()
        self.play_button.hide()
        self.pause_button.hide()
        self.media_player.stop()

        self.text_widget.setHtml(html)
        self.text_widget.show()

    def show_video(self, media_content):
        self.text_widget.hide()
        self.video_widget.show()
        self.play_button.show()
        self.pause_button.show()

        self.media_player.setMedia(media_content)
        self.media_player.setPosition(0)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trascrizione e Simulazione Conversazione")
        self.setFixedSize(600, 750)
        self.setStyleSheet("background-color: #f0f8ff;")
        self.current_card_index = 1
        self.card_data = [
            ("Simulazione Avatar", "Video/simulazione animata della conversazione..."),
            ("Trascrizione", "Testo della conversazione trascritto..."),
            ("Sintesi", "Riassunto della conversazione tra paziente e dottore...")
        ]
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)

        logo = QLabel()
        logo.setPixmap(QPixmap('frontend/icons/logo.png').scaled(250, 250, Qt.KeepAspectRatio))

        menu_button = QPushButton()
        menu_button.setCursor(Qt.PointingHandCursor)
        menu_button.setStyleSheet("background-color: transparent; border: none;")
        menu_button.setIcon(QIcon("frontend/icons/menu_icon.png"))
        menu_button.setIconSize(QSize(20, 20))

        top_bar.addWidget(logo, alignment=Qt.AlignLeft)
        top_bar.addWidget(menu_button, alignment=Qt.AlignRight)

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
        self.download_button.clicked.connect(self.download_files)
        self.download_button.hide()


        self.card = Card()
        self.card.hide()

        navigation = QHBoxLayout()
        prev_btn = QPushButton()
        prev_btn.setIcon(QIcon('frontend/icons/left_arrow.png'))
        prev_btn.setCursor(Qt.PointingHandCursor)
        prev_btn.setStyleSheet("background-color: transparent; border: none;")
        prev_btn.clicked.connect(self.prev_card)

        next_btn = QPushButton()
        next_btn.setIcon(QIcon('frontend/icons/right_arrow.png'))
        next_btn.setCursor(Qt.PointingHandCursor)
        next_btn.setStyleSheet("background-color: transparent; border: none;")
        next_btn.clicked.connect(self.next_card)

        navigation.addWidget(prev_btn)
        navigation.addStretch()
        self.dots = []
        for _ in self.card_data:
            dot = QLabel("●")
            dot.setStyleSheet("color: lightgray; font-size: 20px;")
            self.dots.append(dot)
            navigation.addWidget(dot, alignment=Qt.AlignCenter)
        navigation.addStretch()
        navigation.addWidget(next_btn)

        main_layout.addLayout(top_bar)
        main_layout.addStretch()
        center_layout = QHBoxLayout()
        center_layout.addWidget(self.record_button)
        center_layout.addWidget(self.download_button)
        main_layout.addLayout(center_layout)
        main_layout.addStretch()
        main_layout.addWidget(self.card, alignment=Qt.AlignCenter)
        main_layout.addLayout(navigation)

        self.setLayout(main_layout)

    def toggle_recording(self):
        self.record_button.toggle_recording()
        if not self.record_button.recording:
            self.show_card()
            self.download_button.show()
        else:
            self.card.hide()
            self.download_button.hide()

    def show_card(self):
        global output
        if self.current_card_index == 1:
            self.card.show_text(output[1])
        elif self.current_card_index == 0:
            self.card.show_video(output[0])
        elif self.current_card_index == 2:
            self.card.show_text(output[2])
        self.update_dots()
        self.card.show()

    def update_dots(self):
        for i, dot in enumerate(self.dots):
            if i == self.current_card_index:
                dot.setStyleSheet("color: #bbdefb; font-size: 20px;")
            else:
                dot.setStyleSheet("color: lightgray; font-size: 20px;")

    def next_card(self):
        if self.current_card_index < len(self.card_data) - 1:
            self.current_card_index += 1
            self.show_card()

    def prev_card(self):
        if self.current_card_index > 0:
            self.current_card_index -= 1
            self.show_card()

    def download_files(self):
        file_url = 'file://' + pathname2url(os.path.abspath('temp.html'))

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(file_url)
            page.pdf(path="output.pdf", format="A4")
            browser.close()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
