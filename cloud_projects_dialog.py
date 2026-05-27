import requests
from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QLabel, QListWidgetItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

class CloudProjectsDialog(QDialog):
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.selected_project = None
        self.projects = []
        
        self.setWindowTitle("Browse Cloud Projects")
        self.setMinimumSize(450, 350)
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QLabel { color: #2D3748; font-weight: bold; font-size: 14px; }
            QListWidget { border: 1px solid #CBD5E0; border-radius: 5px; padding: 5px; font-size: 14px; }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #E2E8F0; }
            QListWidget::item:selected { background-color: #E6F2F3; color: #007B83; font-weight: bold; }
            QPushButton { background-color: #007B83; color: white; border-radius: 5px; padding: 10px; font-weight: bold; }
            QPushButton:hover { background-color: #00636a; }
            QPushButton:disabled { background-color: #A0AEC0; }
        """)

        layout = QVBoxLayout(self)
        
        self.status_label = QLabel("Fetching your cloud projects...")
        layout.addWidget(self.status_label)

        self.list_widget = QListWidget()
        self.list_widget.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.list_widget)

        self.download_btn = QPushButton("Download and Open Project")
        self.download_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self.accept_download)
        layout.addWidget(self.download_btn)

        # Load projects automatically
        self.load_projects()

    def load_projects(self):
        try:
            res = requests.post("https://mouse-pose.com/api/user/data", json={"userId": self.user_data['id']}, timeout=5)
            res.raise_for_status()
            self.projects = res.json().get('projects', [])
            
            if not self.projects:
                self.status_label.setText("No cloud projects found.")
                return
                
            self.status_label.setText("Select a project to download to your PC:")
            
            for p in reversed(self.projects): # Show newest first
                item = QListWidgetItem(f"📁 {p['name']} (Synced: {p['date']})")
                item.setData(Qt.UserRole, p)
                self.list_widget.addItem(item)
                
        except Exception as e:
            self.status_label.setText("Failed to connect to the cloud.")
            self.status_label.setStyleSheet("color: #E53E3E;")

    def on_selection_changed(self):
        self.download_btn.setEnabled(len(self.list_widget.selectedItems()) > 0)

    def accept_download(self):
        selected_item = self.list_widget.selectedItems()[0]
        self.selected_project = selected_item.data(Qt.UserRole)
        self.accept()