import requests
import time
from PySide6.QtWidgets import QDialog, QLineEdit, QVBoxLayout, QDialogButtonBox, QLabel, QPushButton, QApplication
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        loader = QUiLoader()
        ui_widget = loader.load("login_dialog.ui", self)
        
        layout = QVBoxLayout(self)
        layout.addWidget(ui_widget)
        self.setLayout(layout)

        self.emailEdit = ui_widget.findChild(QLineEdit, "emailEdit")
        self.passwordEdit = ui_widget.findChild(QLineEdit, "passwordEdit")
        self.buttonBox = ui_widget.findChild(QDialogButtonBox, "buttonBox")
        self.statusLabel = ui_widget.findChild(QLabel, "statusLabel")
        
        # Make the register link look like a pointing hand when hovered
        self.registerLabel = ui_widget.findChild(QLabel, "registerLabel")
        if self.registerLabel:
            self.registerLabel.setCursor(QCursor(Qt.PointingHandCursor))
            self.registerLabel.setFocusPolicy(Qt.NoFocus)

        # Get the actual login button so we can disable it during the request
        self.login_btn = None
        cancel_button = None
        
        # Dynamically find the accept and reject buttons regardless of their standard name (Ok, Save, etc.)
        for btn in self.buttonBox.buttons():
            role = self.buttonBox.buttonRole(btn)
            if role == QDialogButtonBox.AcceptRole:
                self.login_btn = btn
            elif role == QDialogButtonBox.RejectRole:
                cancel_button = btn

        if self.login_btn is None:
            self.login_btn = QPushButton("Sign In")
            self.buttonBox.addButton(self.login_btn, QDialogButtonBox.AcceptRole)
        else:
            self.login_btn.setText("Sign In")

        self.login_btn.setCursor(QCursor(Qt.PointingHandCursor))

        if cancel_button:
            cancel_button.setCursor(QCursor(Qt.PointingHandCursor))

        # Store user data upon successful login
        self.user_data = None 

        # Connections
        self.buttonBox.accepted.connect(self.attempt_login)
        self.buttonBox.rejected.connect(self.reject)

    def attempt_login(self):
        email = self.emailEdit.text().strip()
        password = self.passwordEdit.text()

        if not email or not password:
            self.statusLabel.setText("Please enter both email and password.")
            self.statusLabel.setStyleSheet("color: #E53E3E;") # Red error text
            return

        self.statusLabel.setText("Connecting to server...")
        self.statusLabel.setStyleSheet("color: #718096;") # Gray loading text
        
        if self.login_btn:
            self.login_btn.setEnabled(False) # Prevent double clicks
            
        self.repaint() # Force UI to update

        # --- Actual HTTP Request to Next.js API ---
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                if attempt > 1:
                    self.statusLabel.setText(f"Waking up server... (Retry {attempt}/{max_retries})")
                    QApplication.processEvents() # Keep UI responsive while waiting
                    time.sleep(2) # Give the serverless function time to boot
                    
                url = "http://mouse-pose.com/api/auth/login" 
                payload = {"email": email, "password": password}
                
                # Increased timeout to 15s to seamlessly absorb most Vercel cold starts
                response = requests.post(url, json=payload, timeout=15)
                data = response.json()

                if response.status_code == 200:
                    self.statusLabel.setText("Login successful!")
                    self.statusLabel.setStyleSheet("color: #38A169;") # Green success text
                    self.user_data = data.get("user") 
                    self.accept()
                    return
                elif response.status_code >= 500:
                    # Server errors (5xx) often mean a Gateway Timeout during boot. We retry
                    if attempt == max_retries:
                        error_msg = data.get("error", "Server Error. Please try again.")
                        self.statusLabel.setText(error_msg)
                        self.statusLabel.setStyleSheet("color: #E53E3E;")
                        if self.login_btn: self.login_btn.setEnabled(True)
                    continue 
                else:
                    # Client errors (e.g., 401 wrong password) shouldn't be retried
                    error_msg = data.get("error", "Login failed.")
                    self.statusLabel.setText(error_msg)
                    self.statusLabel.setStyleSheet("color: #E53E3E;")
                    if self.login_btn: self.login_btn.setEnabled(True)
                    return

            except requests.exceptions.RequestException as e:
                # Network timeout or offline server
                if attempt == max_retries:
                    self.statusLabel.setText("Server offline or taking too long. Is Next.js running?")
                    self.statusLabel.setStyleSheet("color: #E53E3E;")
                    if self.login_btn: self.login_btn.setEnabled(True)
                    return