import os
import shutil
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QHBoxLayout, QTextEdit, QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt5.QtCore import Qt, QUrl, QSize
from PyQt5.QtGui import QIcon, QPixmap, QColor
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from playwright.sync_api import sync_playwright
from urllib.request import pathname2url
from pathlib import Path
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from handle_video import info_video



def get_output_from_folder_path(path):
    with open(path + '/conversation.txt') as c:
        conversation = c.read()
    with open(path + "/notes.txt") as n:
        notes = n.read()
    return [path, conversation, notes]


def download_files(conversation_path, video_path, video_path_2, notes_path, file_name):

    temp_notes_text = ""
    temp_notes_path = "./temp_files/temp_notes.html"
    temp_conversation_text = ""
    temp_conversation_path = "./temp_files/temp_conversation.html"

    with open(notes_path, "r") as f:
        temp_notes_text = f.read()

    with open(temp_notes_path, "w", encoding="utf-8") as f:
        f.write(temp_notes_text)

    with open(conversation_path, "r") as f:
        temp_conversation_text = f.read()
    
    with open(temp_conversation_path, "w", encoding="utf-8") as f:
        f.write(temp_conversation_text)

    downloads_folder = Path.home() / "Downloads"
    save_folder = downloads_folder / f"AINotes_{file_name}"



    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('file://' + pathname2url(os.path.abspath(temp_notes_path)))
        pdf_path = save_folder / "notes.pdf"
        page.pdf(path=pdf_path, format="A4")
        page.goto('file://' + pathname2url(os.path.abspath(temp_conversation_path)))
        pdf_path = save_folder / "conversation.pdf"
        page.pdf(path=pdf_path, format="A4")
        browser.close()
    
    download_video2_path = save_folder / "videoT.mp4"
    shutil.copy(video_path_2, download_video2_path)

    if os.path.exists(video_path):
        download_video_path = save_folder / "video.mp4"
        shutil.copy(video_path, download_video_path)


        

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

    def show_video(self, path):
        self.video_check = True
        print(path)
        save_time = path.split("/")[-1]
        print("SAVETIME " + save_time)

        self.video_check = True
        # Verifica se esiste il file "video.mp4"
        if os.path.exists(path + "/video.mp4"):
            self.video = QMediaContent(QUrl.fromLocalFile(os.path.abspath(path + "/video.mp4")))
        else:
            # Legge il contenuto del file "id.txt"
            with open(path + "/id.txt", "r", encoding="utf-8") as file:
                id = file.read().strip()
                check = info_video(id, save_time)
                print(check)
                if check:
                    self.video = QMediaContent(QUrl.fromLocalFile(os.path.abspath(path + "/video.mp4")))
                else:
                    self.video = QMediaContent(QUrl.fromLocalFile(os.path.abspath(path + "/videoT.mp4")))

        video_path = os.path.abspath(path + "/videoT.mp4")
        print("Percorso assoluto:", video_path)
        print("Esiste il file:", os.path.exists(video_path))

        self.text_widget.hide()
        self.video_widget.show()
        self.play_button.show()
        self.pause_button.show()
        self.media_player.setMedia(self.video)
        self.media_player.setPosition(0)
        self.media_player.play()


        print("Media status:", self.media_player.mediaStatus())
        print("Is video available:", self.media_player.isVideoAvailable())


class FolderContentWindow(QWidget):
    def __init__(self, folder_path, folder_name, archivie_window):
        super().__init__()
        self.archivie_window = archivie_window
        self.setWindowTitle("AIDOCTORNOTES")
        self.setFixedSize(600, 750)
        self.setStyleSheet("background-color: #f0f8ff;")

        self.output = get_output_from_folder_path(folder_path)
        print(self.output)
        self.main_layout = QVBoxLayout(self)

        header = QHBoxLayout()
        header.setContentsMargins(0,0,0,0)
        self.back_button = QPushButton()
        self.back_button.setIcon(QIcon("frontend/icons/left_arrow.png"))
        self.back_button.setFixedSize(30,30)
        self.back_button.setStyleSheet("background-color: transparent; border: none;")
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.clicked.connect(self.return_to_main)

        logo = QLabel()
        logo.setPixmap(QPixmap('frontend/icons/logo_img_only.png').scaled(30, 30, Qt.KeepAspectRatio))

        header.addWidget(self.back_button, alignment=Qt.AlignLeft)
        header.addStretch()
        header.addWidget(logo, alignment=Qt.AlignRight)
        self.main_layout.addLayout(header)
        
        if os.path.exists(folder_path):
            items = os.listdir(folder_path)

        
        #SETUP

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
        self.download_button.clicked.connect(lambda _, c=folder_path + "/conversation.txt", v=folder_path + "/video.mp4", v2=folder_path + "/videoT.mp4", n=folder_path + "/notes.txt", f=folder_name: download_files(c,v,v2,n,f))


        self.card_data = ["a", "b", "c"]
        self.nav_labels = ["VIDEO", "CONVERSATION", "DOCTOR'S NOTES"]
        self.card = Card()
        self.current_card_index = 1
        self.card.show_text(self.output[1])

        navigation = QHBoxLayout()
        navigation_left = QVBoxLayout()
        navigation_right = QVBoxLayout()
        
        self.prev_text = QLabel(self.nav_labels[0])
        self.prev_text.setAlignment(Qt.AlignCenter)
        self.prev_text.setStyleSheet("font-size: 10px; color: #0d47a1; font-weight: bold")
        self.prev_text.setFixedWidth(100) 
        self.prev_btn = QPushButton()
        self.prev_btn.setIcon(QIcon('frontend/icons/left_arrow.png'))
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.setStyleSheet("background-color: transparent; border: none;")
        self.prev_btn.clicked.connect(self.prev_card)
        navigation_left.addWidget(self.prev_text)
        navigation_left.addWidget(self.prev_btn)

        self.next_text = QLabel(self.nav_labels[2])
        self.next_text.setAlignment(Qt.AlignCenter)
        self.next_text.setStyleSheet("font-size: 10px; color: #0d47a1; font-weight: bold")
        self.next_text.setFixedWidth(100) 
        self.next_btn = QPushButton()
        self.next_btn.setIcon(QIcon('frontend/icons/right_arrow.png'))
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setStyleSheet("background-color: transparent; border: none;")
        self.next_btn.clicked.connect(self.next_card)
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
        self.update_dots()
        navigation.addStretch()
        navigation.addLayout(navigation_right)
        self.main_layout.addStretch()

        self.main_layout.addWidget(self.download_button, alignment=Qt.AlignCenter)
        self.main_layout.addWidget(self.card, alignment=Qt.AlignCenter)
        self.main_layout.addLayout(navigation)


        self.setLayout(self.main_layout)


    def return_to_main(self):
            self.close()
            self.archivie_window.show()

    def show_card(self):
        if self.current_card_index == 1:
            self.card.show_text(self.output[1])
        elif self.current_card_index == 0:
            self.card.show_video(self.output[0])
        elif self.current_card_index == 2:
            self.card.show_text(self.output[2])
        self.update_dots()
        self.update_nav()
        self.card.show()

    def update_nav(self):
        if self.current_card_index == 0:
            self.prev_btn.setDisabled(True)
            self.prev_text.setText("")
            self.next_text.setText(self.nav_labels[1])
        elif self.current_card_index == 2:
            self.next_btn.setDisabled(True)
            self.next_text.setText("")
            self.prev_text.setText(self.nav_labels[1])
        else:
            self.prev_btn.setDisabled(False)
            self.prev_text.show()
            self.next_btn.setDisabled(False)
            self.next_text.show()
            self.prev_text.setText(self.nav_labels[0])
            self.next_text.setText(self.nav_labels[2])


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
