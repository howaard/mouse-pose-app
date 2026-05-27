import sys
import os
import re
from PySide6.QtWidgets import QDialog, QLineEdit, QVBoxLayout, QDialogButtonBox, QLabel
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

class NewProjectDialog(QDialog):
    """
    A dialog for creating a new project inside the dedicated Projects folder.
    """
    def __init__(self, parent=None, projects_root=None): # Accept projects_root
        super().__init__(parent)

        self.projects_path = projects_root # Store the path

        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        loader = QUiLoader()
        ui_widget = loader.load("new_project_dialog.ui", self)

        self.setWindowTitle("Create New Project")
        layout = QVBoxLayout(self)
        layout.addWidget(ui_widget)
        self.setLayout(layout)

        # Find widgets
        self.projectNameEdit = ui_widget.findChild(QLineEdit, "projectNameEdit")
        self.projectPathEdit = ui_widget.findChild(QLineEdit, "projectPathEdit")
        self.buttonBox = ui_widget.findChild(QDialogButtonBox, "buttonBox")
        self.statusLabel = ui_widget.findChild(QLabel, "statusLabel")
        
        # --- Set Path and Make Read-Only ---
        self.projectPathEdit.setText(self.projects_path)
        self.projectPathEdit.setReadOnly(True)

        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        cancel_button = self.buttonBox.button(QDialogButtonBox.Cancel)
        self.ok_button.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_button.setCursor(QCursor(Qt.PointingHandCursor))

        # --- Field Validation ---
        self.ok_button.setEnabled(False)
        self.statusLabel.setText("")
        self.projectNameEdit.textChanged.connect(self.validate_fields)
        
        # Connect signals to slots
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def validate_fields(self):
        """
        Validates project name against the fixed project path.
        """
        project_name = self.projectNameEdit.text().strip()
        
        if not project_name:
            self.ok_button.setEnabled(False)
            self.statusLabel.setText("")
            return

        invalid_chars = re.search(r'[<>:"/\\|?*]', project_name)
        if invalid_chars:
            self.statusLabel.setText(f"Error: Name contains invalid character: '{invalid_chars.group(0)}'")
            self.statusLabel.setStyleSheet("color: #E53E3E;")
            self.ok_button.setEnabled(False)
            return

        # Use the stored projects_path for the check
        full_path = os.path.join(self.projects_path, project_name)
        if os.path.exists(full_path):
            self.statusLabel.setText("Error: A folder with this name already exists.")
            self.statusLabel.setStyleSheet("color: #E53E3E;")
            self.ok_button.setEnabled(False)
            return

        self.statusLabel.setText("Ready to create project.")
        self.statusLabel.setStyleSheet("color: #38A169;")
        self.ok_button.setEnabled(True)

    def get_project_data(self):
        return {
            "name": self.projectNameEdit.text().strip(),
            "path": self.projects_path
        }
