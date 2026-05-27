from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Signal

class ToggleSwitch(QWidget):
    """
    A custom segmented button toggle switch.
    Emits a state_changed signal with the name of the active button.
    """
    state_changed = Signal(str)

    def __init__(self, option1="Overlay", option2="3D Skeleton"):
        super().__init__()
        self.option1_text = option1
        self.option2_text = option2

        self.button1 = QPushButton(self.option1_text)
        self.button2 = QPushButton(self.option2_text)

        self.button1.setCheckable(True)
        self.button2.setCheckable(True)

        self.button1.clicked.connect(lambda: self.on_button_clicked(self.button1))
        self.button2.clicked.connect(lambda: self.on_button_clicked(self.button2))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.button1)
        layout.addWidget(self.button2)
        self.setLayout(layout)
        
        self.setStyleSheet("""
                    QPushButton {
                        background-color: #FFFFFF;
                        color: #007B83;
                        border: 2px solid #007B83;
                        padding: 8px;
                        font-size: 14px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #E6F2F3;
                    }
                    QPushButton:checked {
                        background-color: #007B83;
                        color: #FFFFFF;
                        border: 2px solid #007B83;
                    }
                    QPushButton:first-child {
                        border-top-left-radius: 8px;
                        border-bottom-left-radius: 8px;
                        border-right: none; /* Merges the inner border */
                    }
                    QPushButton:last-child {
                        border-top-right-radius: 8px;
                        border-bottom-right-radius: 8px;
                    }
                """)

        # Set initial state
        self.button1.setChecked(True)

    def on_button_clicked(self, clicked_button):
        if clicked_button == self.button1:
            self.button2.setChecked(False)
            self.button1.setChecked(True) # Ensure it stays checked
            self.state_changed.emit(self.option1_text)
        else:
            self.button1.setChecked(False)
            self.button2.setChecked(True) # Ensure it stays checked
            self.state_changed.emit(self.option2_text)
            
    def setEnabled(self, enabled):
        """Override setEnabled to control both buttons."""
        super().setEnabled(enabled)
        self.button1.setEnabled(enabled)
        self.button2.setEnabled(enabled)
