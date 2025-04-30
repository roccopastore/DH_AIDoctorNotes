import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QHBoxLayout,
    QVBoxLayout, QStackedWidget, QFrame, QSizePolicy, QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, QParallelAnimationGroup, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QPixmap, QConicalGradient, QIcon

class RecordingButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recording = False
        self.spinner_angle = 0
        self.spinner_opacity = 0.0
        # Timer for spinner
        self.spin_timer = QTimer(self)
        self.spin_timer.timeout.connect(self.rotate_spinner)
        # Animation to expand/shrink
        self._size_anim = QPropertyAnimation(self, b"minimumSize")
        self._size_anim.setDuration(200)
        self._size_anim.setEasingCurve(QEasingCurve.OutCubic)
        # Initial appearance
        self.setFixedSize(80, 80)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(self.base_style())
        # Shadow
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
                background-color: #f0f8ff; /* light background */
                border: 4px solid #bbdefb; /* light blue border */
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
            # expand slightly
            self._size_anim.stop()
            self._size_anim.setStartValue(self.size())
            self._size_anim.setEndValue(self.size() + QSize(10, 10))
            self._size_anim.start()
            self.spin_timer.start(16)
        else:
            self.setIcon(QIcon('frontend/icons/mic_icon.png'))
            self.setIconSize(QSize(40, 40))
            # shrink back
            self._size_anim.stop()
            self._size_anim.setStartValue(self.size())
            self._size_anim.setEndValue(QSize(80, 80))
            self._size_anim.start()
            self.spin_timer.stop()
            self.spinner_opacity = 0.0
            self.spinner_angle = 0
            self.update()

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
            # spinner gradient around border
            gradient = QConicalGradient(self.rect().center(), self.spinner_angle)
            gradient.setColorAt(0.0, QColor(85, 214, 121, int(self.spinner_opacity * 255)))
            gradient.setColorAt(0.25, QColor(85, 214, 121, 0))
            pen = QPen(QBrush(gradient), 6)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            # draw arc full circle
            radius = min(self.width(), self.height()) / 2 - 3
            painter.drawEllipse(self.rect().center(), int(radius), int(radius))

class Card(QFrame):
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 20px;
            }
            QLabel {
                color: #0d47a1;
            }
        """)
        # Ombra migliorata
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 20)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        titleLabel = QLabel(f"<b>{title}</b>")
        titleLabel.setStyleSheet("font-size: 20px;")
        contentLabel = QLabel(content)
        contentLabel.setStyleSheet("font-size: 14px;")
        contentLabel.setWordWrap(True)

        layout.addWidget(titleLabel)
        layout.addSpacing(10)
        layout.addWidget(contentLabel)
        self.setLayout(layout)
        self.setFixedSize(400, 500)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trascrizione e Simulazione Conversazione")
        self.setGeometry(100, 100, 600, 800)
        self.setStyleSheet("background-color: #f0f8ff;")
        self.current_card = 0
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        top_bar = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(QPixmap('frontend/icons/logo.png').scaled(250, 250, Qt.KeepAspectRatio))
        menu_button = QPushButton()
        menu_button.setCursor(Qt.PointingHandCursor)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 50))
        menu_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f8ff;
                color: #0d47a1;
                font-size: 16px;
                border-radius:1200px;
                padding:5px;
            }
            QPushButton:hover {
                border-color: #90caf9;
            }
            QPushButton:pressed {
                border-color: #64b5f6;
            }
        """)
        menu_button.setIcon(QIcon("frontend/icons/menu_icon.png"))
        menu_button.setIconSize(QSize(20, 20))
        top_bar.addWidget(logo, alignment=Qt.AlignLeft)
        top_bar.addStretch()
        top_bar.addWidget(menu_button, alignment=Qt.AlignRight)

        self.record_button = RecordingButton()
        self.record_button.clicked.connect(self.toggle_recording)

        self.cards_stack = QStackedWidget()
        self.cards_stack.hide()

        nav_layout = QHBoxLayout()
        nav_layout.addStretch()
        self.dots = []
        for i in range(3):
            dot = QLabel("●")
            dot.setStyleSheet("color: lightgray; font-size: 16px;")
            self.dots.append(dot)
            nav_layout.addWidget(dot, alignment=Qt.AlignCenter)
        nav_layout.addStretch()

        navigation = QHBoxLayout()
        self.prev_btn = QPushButton("<")
        self.prev_btn.setObjectName("prevButton")
        self.prev_btn.setFixedSize(40, 40)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #bbdefb;
                color: #0d47a1;
                border-radius: 20px;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #90caf9;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #999999;
            }
        """)
        self.next_btn = QPushButton(">")
        self.next_btn.setObjectName("nextButton")
        self.next_btn.setFixedSize(40, 40)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: #bbdefb;
                color: #0d47a1;
                border-radius: 20px;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #90caf9;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #999999;
            }
        """)
        self.prev_btn.clicked.connect(self.prev_card)
        self.next_btn.clicked.connect(self.next_card)
        navigation.addWidget(self.prev_btn)
        navigation.addStretch()
        navigation.addWidget(self.next_btn)

        main_layout.addLayout(top_bar)
        main_layout.addStretch()
        main_layout.addWidget(self.record_button, alignment=Qt.AlignCenter)
        main_layout.addStretch()
        main_layout.addWidget(self.cards_stack, alignment=Qt.AlignCenter)
        main_layout.addLayout(nav_layout)
        main_layout.addLayout(navigation)

        self.setLayout(main_layout)

    def toggle_recording(self):
        self.record_button.toggle_recording()
        if not self.record_button.recording:
            self.show_cards()
        else:
            self.cards_stack.hide()

    def animate_card_transition(self, index):
        current = self.cards_stack.currentWidget()
        target = self.cards_stack.widget(index)

        if current == target:
            return

        # Disabilita i bottoni durante l'animazione
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)

        # Imposta l'indice corrente subito
        self.cards_stack.setCurrentIndex(index)

        # Posiziona la carta target fuori schermo
        direction = 1 if index > self.cards_stack.currentIndex() else -1
        target.setGeometry(QRect(400 * direction, 0, 400, 500))
        target_opacity = QGraphicsOpacityEffect()
        target_opacity.setOpacity(0.0)
        target.setGraphicsEffect(target_opacity)

        # Animazioni per la carta uscente
        anim_out_pos = QPropertyAnimation(current, b"pos")
        anim_out_pos.setDuration(600)
        anim_out_pos.setEasingCurve(QEasingCurve.InOutCubic)
        anim_out_pos.setEndValue(QPoint(-400 * direction, 0))

        anim_out_opacity = QPropertyAnimation(current.graphicsEffect(), b"opacity")
        anim_out_opacity.setDuration(600)
        anim_out_opacity.setEasingCurve(QEasingCurve.InOutCubic)
        anim_out_opacity.setStartValue(1.0)
        anim_out_opacity.setEndValue(0.0)

        anim_out_scale = QPropertyAnimation(current, b"geometry")
        anim_out_scale.setDuration(600)
        anim_out_scale.setEasingCurve(QEasingCurve.InOutCubic)
        anim_out_scale.setStartValue(QRect(current.pos().x(), 0, 400, 500))
        anim_out_scale.setEndValue(QRect(current.pos().x(), 0, int(400 * 0.9), int(500 * 0.9)))

        # Animazioni per la carta entrante
        anim_in_pos = QPropertyAnimation(target, b"pos")
        anim_in_pos.setDuration(600)
        anim_in_pos.setEasingCurve(QEasingCurve.OutBack)
        anim_in_pos.setStartValue(QPoint(400 * direction, 0))
        anim_in_pos.setEndValue(QPoint(0, 0))

        anim_in_opacity = QPropertyAnimation(target_opacity, b"opacity")
        anim_in_opacity.setDuration(600)
        anim_in_opacity.setEasingCurve(QEasingCurve.InOutCubic)
        anim_in_opacity.setStartValue(0.0)
        anim_in_opacity.setEndValue(1.0)

        anim_in_scale = QPropertyAnimation(target, b"geometry")
        anim_in_scale.setDuration(600)
        anim_in_scale.setEasingCurve(QEasingCurve.OutBack)
        anim_in_scale.setStartValue(QRect(target.pos().x(), 0, int(400 * 0.9), int(500 * 0.9)))
        anim_in_scale.setEndValue(QRect(target.pos().x(), 0, 400, 500))

        # Gruppo di animazioni parallele
        anim_group = QParallelAnimationGroup()
        anim_group.addAnimation(anim_out_pos)
        anim_group.addAnimation(anim_out_opacity)
        anim_group.addAnimation(anim_out_scale)
        anim_group.addAnimation(anim_in_pos)
        anim_group.addAnimation(anim_in_opacity)
        anim_group.addAnimation(anim_in_scale)

        # Aggiorna i dots e riabilita i bottoni al termine
        anim_group.finished.connect(self.update_dots)
        anim_group.finished.connect(lambda: self.prev_btn.setEnabled(True))
        anim_group.finished.connect(lambda: self.next_btn.setEnabled(True))

        anim_group.start()

    def show_cards(self):
        while self.cards_stack.count():
            widget = self.cards_stack.widget(0)
            self.cards_stack.removeWidget(widget)

        transcription_card = Card("Trascrizione", "Testo della conversazione trascritto...")
        simulation_card = Card("Simulazione Avatar", "Video/simulazione animata della conversazione...")
        summary_card = Card("Sintesi", "Riassunto della conversazione tra paziente e dottore...")

        self.cards_stack.addWidget(simulation_card)
        self.cards_stack.addWidget(transcription_card)
        self.cards_stack.addWidget(summary_card)

        self.current_card = 1
        self.update_dots()
        self.cards_stack.setCurrentIndex(self.current_card)
        self.cards_stack.show()

        for i in range(self.cards_stack.count()):
            effect = QGraphicsOpacityEffect()
            effect.setOpacity(1.0 if i == self.current_card else 0.0)
            self.cards_stack.widget(i).setGraphicsEffect(effect)

    def update_dots(self):
        for i, dot in enumerate(self.dots):
            if i == self.current_card:
                dot.setStyleSheet("color: #0d47a1; font-size: 18px;")
            else:
                dot.setStyleSheet("color: lightgray; font-size: 16px;")

    def next_card(self):
        if self.current_card < self.cards_stack.count() - 1:
            self.current_card += 1
            self.animate_card_transition(self.current_card)

    def prev_card(self):
        if self.current_card > 0:
            self.current_card -= 1
            self.animate_card_transition(self.current_card)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())