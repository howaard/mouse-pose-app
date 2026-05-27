import sys
import os
from PySide6.QtWidgets import QMainWindow, QLabel, QPushButton, QFileDialog, QApplication, QHBoxLayout, QProgressDialog
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QPixmap, QCursor
from PySide6.QtCore import Qt, QThread
from cloud_projects_dialog import CloudProjectsDialog 
from download_worker import DownloadWorker 

from new_project_dialog import NewProjectDialog
from main_window import MainWindow 
from login_dialog import LoginDialog

class WelcomeWindow(QMainWindow):
    def __init__(self, app_root=None, projects_root=None):
        super().__init__()
        
        self.app_path = app_root
        self.projects_path = projects_root
        self.user_data = None # Store the logged-in user

        loader = QUiLoader()
        ui_widget = loader.load("welcome_window.ui", self)
        self.setCentralWidget(ui_widget)
        self.setWindowTitle("Monocular 3D Mouse Pose Estimation")

        self.logoLabel = ui_widget.findChild(QLabel, "logoLabel")
        self.original_pixmap = QPixmap("assets/logo.png") 
        create_button = ui_widget.findChild(QPushButton, "createProjectButton")
        open_button = ui_widget.findChild(QPushButton, "openProjectButton")
        self.subtitleLabel = ui_widget.findChild(QLabel, "subtitleLabel")

        # Dynamically insert the Cloud Download Button
        self.cloud_button = QPushButton("Browse Cloud Projects")
        self.cloud_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.cloud_button.setStyleSheet("background-color: #E6F2F3; color: #007B83; border: 1px solid #007B83;")
        self.cloud_button.clicked.connect(self.browse_cloud_projects)
        
        # Find the layout holding the buttons and insert our new button
        h_layout = ui_widget.findChild(QHBoxLayout, "horizontalLayout")
        if h_layout:
            h_layout.insertWidget(2, self.cloud_button) # Insert next to 'Open'

        create_button.setCursor(QCursor(Qt.PointingHandCursor))
        open_button.setCursor(QCursor(Qt.PointingHandCursor))
        create_button.clicked.connect(self.create_new_project)
        open_button.clicked.connect(self.open_existing_project)

        self.loginButton = ui_widget.findChild(QPushButton, "loginButton")
        if self.loginButton:
            self.loginButton.clicked.connect(self.open_login_dialog)

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, '_centered'):
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
            self._centered = True
        self.resize_logo()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_logo()

    def resize_logo(self):
        if hasattr(self, 'logoLabel') and self.logoLabel and self.logoLabel.width() > 0:
            label_size = self.logoLabel.size()
            scaled_pixmap = self.original_pixmap.scaled(
                label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logoLabel.setPixmap(scaled_pixmap)

    def create_new_project(self):
        dialog = NewProjectDialog(self, projects_root=self.projects_path)
        if dialog.exec():
            project_data = dialog.get_project_data()
            full_project_path = os.path.join(self.projects_path, project_data['name'])
            try:
                os.makedirs(os.path.join(full_project_path, 'input'), exist_ok=True)
                os.makedirs(os.path.join(full_project_path, 'output'), exist_ok=True)
                project_data['full_path'] = full_project_path
                self.open_main_window(project_data)
            except OSError as e:
                self.subtitleLabel.setText(f"Error: Could not create project folder.")
                self.subtitleLabel.setStyleSheet("color: #E53E3E;")

    def open_existing_project(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Project Folder", self.projects_path)
        if directory:
            norm_selected_path = os.path.normcase(os.path.normpath(directory))
            norm_projects_path = os.path.normcase(os.path.normpath(self.projects_path))
            parent_dir = os.path.normcase(os.path.normpath(os.path.dirname(norm_selected_path)))

            if parent_dir != norm_projects_path:
                self.subtitleLabel.setText("Error: Please select a direct project folder inside 'projects'.")
                self.subtitleLabel.setStyleSheet("color: #E53E3E;")
                return

            self.subtitleLabel.setText("A lightweight tool for markerless 3D animal pose tracking.")
            self.subtitleLabel.setStyleSheet("")

            project_data = {"name": os.path.basename(directory), "full_path": directory}
            self.open_main_window(project_data)

    def browse_cloud_projects(self):
        if not self.user_data:
            self.subtitleLabel.setText("You must Log In to browse cloud projects.")
            self.subtitleLabel.setStyleSheet("color: #E53E3E;")
            return

        dialog = CloudProjectsDialog(self.user_data, self)
        if dialog.exec():
            selected_project = dialog.selected_project
            if selected_project:
                self.start_download(selected_project)

    def start_download(self, cloud_project):
        self.progress_dialog = QProgressDialog("Connecting to AWS S3...", "Cancel", 0, 0, self)
        self.progress_dialog.setWindowTitle("Downloading Project")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)

        self.download_thread = QThread()
        self.download_worker = DownloadWorker(cloud_project, self.projects_path)
        self.download_worker.moveToThread(self.download_thread)

        self.download_worker.progress_update.connect(self.progress_dialog.setLabelText)
        self.download_worker.finished.connect(self.on_download_finished)

        self.download_thread.started.connect(self.download_worker.run_download)
        self.progress_dialog.canceled.connect(self.download_worker.stop)
        
        self.download_thread.start()

    def on_download_finished(self, success, message, local_project_data):
        self.progress_dialog.close()
        self.download_thread.quit()
        self.download_thread.wait()

        if success:
            self.subtitleLabel.setText("A lightweight tool for markerless 3D animal pose tracking.")
            self.subtitleLabel.setStyleSheet("")
            self.open_main_window(local_project_data)
        else:
            self.subtitleLabel.setText(f"Download failed: {message}")
            self.subtitleLabel.setStyleSheet("color: #E53E3E;")

    def open_main_window(self, project_data):
        # Pass the user_data to the main window
        self.main_win = MainWindow(project_data, app_root=self.app_path, projects_root=self.projects_path, user_data=self.user_data)
        self.main_win.show()
        self.close()
    
    def open_login_dialog(self):
        dialog = LoginDialog(self)
        if dialog.exec():
            # Save the logged-in user data returned from the API
            self.user_data = dialog.user_data 
            self.loginButton.setText("Synced \u2713") 
            self.loginButton.setEnabled(False)