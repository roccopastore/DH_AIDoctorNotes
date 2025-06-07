from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
import os
from datetime import datetime
from folder_content_window import FolderContentWindow


class ArchivieWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("AIDOCTORNOTES")
        self.setFixedSize(600, 750)
        self.setStyleSheet("background-color: #f0f8ff;")

        main_layout = QVBoxLayout(self)

        # --- Header with back button ---
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
        main_layout.addLayout(header)

       # --- Lista scrollabile ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(10)  # Nessuna spaziatura tra gli item
        scroll_layout.setContentsMargins(0, 0, 0, 0)


        # --- Elementi dell'archivio ---
        self.folders = sorted(
            os.listdir('backend/output/saves/'),
            key=lambda x: float(x),  # supponendo che il nome della cartella sia un numero (timestamp)
            reverse=True             # facoltativo: True = ordine decrescente (dal più recente)
        )        
        print(self.folders)

        for folder in self.folders:
            item_layout = QHBoxLayout()

            title = datetime.fromtimestamp(float(folder)).strftime("%Y-%m-%d %H:%M:%S")
            title_label = QLabel(title)
            title_label.setStyleSheet("font-size: 14px; color: #0d47a1; font-weight: bold;")

            open_button = QPushButton()
            open_button.setIcon(QIcon("frontend/icons/right_arrow.png"))
            open_button.setFixedSize(20, 20)
            open_button.setStyleSheet("background-color: transparent; border: none;")
            open_button.setCursor(Qt.PointingHandCursor)
            open_button.clicked.connect(lambda _, f=folder: self.open_folder_window(f))

            item_layout.addWidget(title_label)
            item_layout.addStretch()
            item_layout.addWidget(open_button)

            item_container = QFrame()
            item_container.setFixedHeight(100)  # Dimensione fissa richiesta
            item_container.setLayout(item_layout)
            item_container.setObjectName("archiveItem")
            item_container.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                }
                                         
                #archiveItem {
                    border: 2px solid #7ac5f3;  /* Colore del bordo */
                    border-radius: 15px;        /* Raggio degli angoli */
                    padding: 10px;
                }
            """)

            scroll_layout.addWidget(item_container)

        scroll_content.setLayout(scroll_layout)
        scroll_content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        self.setLayout(main_layout)

    def open_folder_window(self, folder):
        folder_path = os.path.join("backend/output/saves/", folder)
        self.folder_window = FolderContentWindow(folder_path, folder, self)
        self.folder_window.show()
        self.hide()

    def return_to_main(self):
        self.close()
        self.main_window.show()
