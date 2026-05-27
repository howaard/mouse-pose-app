import sys
import os
import shutil
import cv2
import re
import glob
import webbrowser
from PySide6.QtWidgets import (QMainWindow, QLabel, QListWidget, QPushButton, QFileDialog, 
                               QMenuBar, QListWidgetItem, QPlainTextEdit,
                               QComboBox, QHBoxLayout, QVBoxLayout, QWidget,
                               QSizePolicy, QStackedWidget, QSlider, QMessageBox, QDialog)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt, QSize, QThread, QTimer, QUrl
from PySide6.QtGui import QPixmap, QIcon, QScreen, QImage, QColor, QAction, QDesktopServices, QCursor, QPainter

# Import workers and widgets
from pose_worker import PoseWorker
from new_project_dialog import NewProjectDialog
from video_player import VideoPlayer
from skeleton_player import SkeletonPlayer
from sync_worker import SyncWorker 

# --- Advanced Export Dialog ---
class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Frame")
        self.choice = None
        
        layout = QVBoxLayout(self)
        label = QLabel("Select export format:")
        label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2D3748; margin-bottom: 10px;")
        layout.addWidget(label)
        
        btn_style = "background-color: #FFFFFF; color: #007B83; border: 2px solid #007B83; border-radius: 6px; padding: 8px; font-weight: bold;"
        
        btn_left = QPushButton("⬅️ Left Frame Only")
        btn_left.setStyleSheet(btn_style)
        btn_left.clicked.connect(lambda: self.make_choice("left"))
        layout.addWidget(btn_left)
        
        btn_right = QPushButton("➡️ Right Frame Only")
        btn_right.setStyleSheet(btn_style)
        btn_right.clicked.connect(lambda: self.make_choice("right"))
        layout.addWidget(btn_right)
        
        btn_both = QPushButton("↔️ Left + Right (Side-by-Side)")
        btn_both.setStyleSheet(btn_style)
        btn_both.clicked.connect(lambda: self.make_choice("both"))
        layout.addWidget(btn_both)
        
        self.setStyleSheet("QDialog { background-color: #F7FAFC; } QPushButton:hover { background-color: #E6F2F3; }")

    def make_choice(self, choice):
        self.choice = choice
        self.accept()

class MainWindow(QMainWindow):
    def __init__(self, project_data=None, app_root=None, projects_root=None, user_data=None):
        super().__init__()
        
        self.project_data = project_data
        self.app_root = app_root
        self.projects_root = projects_root
        self.user_data = user_data 
        
        self.input_folder = os.path.join(self.project_data['full_path'], 'input')
        self.output_folder = os.path.join(self.project_data['full_path'], 'output')
        self.dlc_model_path = os.path.join(self.app_root, "deeplabcut")

        self.worker_thread = None
        self.pose_worker = None
        self.sync_worker_thread = None
        self.sync_worker = None
        
        self.is_playing = False
        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self.sync_next_frame)
        self.master_fps = 30
        
        self.current_paths = {
            'Original': None,
            '2D Overlay': None,
            '3D Skeleton': None,
            'rig_data': os.path.join(self.app_root, "models", "rig_data.json")
        }
        
        loader = QUiLoader()
        ui_widget = loader.load("main_window.ui", self)
        
        if ui_widget is None:
            raise RuntimeError("Failed to load 'main_window.ui'. Please ensure the file contains valid XML and no unescaped '&' characters in the stylesheet.")
            
        self.setCentralWidget(ui_widget)
        self.setWindowTitle(f"Project: {project_data.get('name', 'Untitled')}")
        self.setAcceptDrops(True)

        self._setup_menu_bar()
        self._find_widgets()
        self._setup_video_players_and_controls()
        self._setup_ui_and_connections()
        
        self.populate_import_list()
        self.populate_output_list()

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, '_is_centered'):
            self.center_window()
            self._is_centered = True
            
    def center_window(self):
        center_point = QScreen.availableGeometry(self.screen()).center()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    # --- Intercept App Exit for Cloud Sync Prompt ---
    def closeEvent(self, event):
        if getattr(self, '_is_closing', False):
            self.cleanup_for_exit()
            event.accept()
            return

        # If logged in and the sync button isn't disabled (meaning sync isn't currently running)
        if self.user_data and getattr(self, 'sync_action', None) and self.sync_action.isEnabled():
            reply = QMessageBox.question(
                self, 'Sync Before Exit?', 
                "Would you like to sync your project to the cloud before exiting?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.exit_after_sync = True
                self.start_cloud_sync()
                event.ignore() # Keep window open while syncing
                return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
                
        self._is_closing = True
        self.cleanup_for_exit()
        event.accept()

    def _setup_menu_bar(self):
        self.menu_bar = QMenuBar()
        self.setMenuBar(self.menu_bar)
        self.menu_bar.setStyleSheet("""
            QMenuBar { background-color: #FFFFFF; color: #2D3748; font-size: 14px; border-bottom: 2px solid #007B83; }
            QMenuBar::item:selected { background-color: #E6F2F3; color: #007B83; }
            QMenu { background-color: #FFFFFF; color: #2D3748; border: 1px solid #CBD5E0; }
            QMenu::item:selected { background-color: #007B83; color: #FFFFFF; }
            QMenu::item:disabled { color: #A0AEC0; }
        """)

        project_menu = self.menu_bar.addMenu("Project")
        
        create_action = QAction("Create New Project...", self)
        create_action.triggered.connect(self.create_new_project_from_menu)
        project_menu.addAction(create_action)

        open_action = QAction("Open Project...", self)
        open_action.triggered.connect(self.open_existing_project_from_menu)
        project_menu.addAction(open_action)

        web_action = QAction("View Web Dashboard", self)
        web_action.triggered.connect(lambda: webbrowser.open("https://mouse-pose.com"))
        project_menu.addAction(web_action)
        
        project_menu.addSeparator()
        self.sync_action = QAction("Sync Project to Cloud", self)
        self.sync_action.triggered.connect(self.start_cloud_sync)
        if not self.user_data:
            self.sync_action.setEnabled(False)
            self.sync_action.setText("Sync Project to Cloud (Login Required)")
        project_menu.addAction(self.sync_action)
        
        project_menu.addSeparator()
        exit_action = QAction("Exit to Welcome Menu", self)
        exit_action.triggered.connect(self.return_to_welcome)
        project_menu.addAction(exit_action)
        
        signout_action = QAction("Sign Out", self)
        signout_action.triggered.connect(self.sign_out)
        if not self.user_data:
            signout_action.setEnabled(False)
        project_menu.addAction(signout_action)
        
    def _find_widgets(self):
        self.projectPathLabel = self.findChild(QLabel, "projectPathLabel")
        self.importListWidget = self.findChild(QListWidget, "importListWidget")
        self.inputChosenLabel = self.findChild(QLabel, "inputChosenLabel")
        self.importButton = self.findChild(QPushButton, "importButton")
        self.removeButton = self.findChild(QPushButton, "removeButton")
        self.poseButton = self.findChild(QPushButton, "poseButton")
        self.modeComboBox = self.findChild(QComboBox, "modeComboBox")
        self.logOutput = self.findChild(QPlainTextEdit, "logOutput")
        
        self.exportFrameButton = self.findChild(QPushButton, "exportFrameButton")
        self.browseFolderButton = self.findChild(QPushButton, "browseFolderButton")
        self.syncCloudButton = self.findChild(QPushButton, "syncCloudButton")
        
        self.resultsListWidget = self.findChild(QListWidget, "resultsListWidget")
        self.deleteRunButton = self.findChild(QPushButton, "deleteRunButton")
        
        self.rewindButton = self.findChild(QPushButton, "rewindButton")
        self.syncPlayButton = self.findChild(QPushButton, "syncPlayButton")
        self.masterSlider = self.findChild(QSlider, "masterSlider")
        self.masterTimeLabel = self.findChild(QLabel, "masterTimeLabel")
        
        self.videoPlayersLayout = self.findChild(QHBoxLayout, "videoPlayersLayout")

    def _setup_video_players_and_controls(self):
        if self.videoPlayersLayout:
            while self.videoPlayersLayout.count():
                item = self.videoPlayersLayout.takeAt(0)
                widget = item.widget()
                if widget: widget.deleteLater()

        self.left_dropdown = QComboBox()
        self.left_dropdown.addItems(["Original", "2D Overlay", "3D Skeleton"])
        self.left_dropdown.setCurrentText("Original")
        self.left_dropdown.currentTextChanged.connect(self.on_left_dropdown_changed)
        
        self.left_video_player = VideoPlayer("")
        self.left_video_player.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.left_video_player.title_label.hide() 
        
        self.left_skeleton_player = SkeletonPlayer("")
        self.left_skeleton_player.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.left_skeleton_player.title_label.hide()

        self.left_stack = QStackedWidget()
        self.left_stack.addWidget(self.left_video_player)
        self.left_stack.addWidget(self.left_skeleton_player)
        self.left_stack.setCurrentWidget(self.left_video_player)
        
        left_container = QVBoxLayout()
        left_container.addWidget(self.left_dropdown)
        left_container.addWidget(self.left_stack)
        
        left_widget = QWidget()
        left_widget.setLayout(left_container)

        self.right_dropdown = QComboBox()
        self.right_dropdown.addItems(["Original", "2D Overlay", "3D Skeleton"])
        self.right_dropdown.setCurrentText("2D Overlay")
        self.right_dropdown.currentTextChanged.connect(self.on_right_dropdown_changed)
        
        self.right_video_player = VideoPlayer("")
        self.right_video_player.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.right_video_player.title_label.hide()
        
        self.right_skeleton_player = SkeletonPlayer("")
        self.right_skeleton_player.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.right_skeleton_player.title_label.hide()

        self.right_stack = QStackedWidget()
        self.right_stack.addWidget(self.right_video_player)
        self.right_stack.addWidget(self.right_skeleton_player)
        self.right_stack.setCurrentWidget(self.right_video_player)
        
        right_container = QVBoxLayout()
        right_container.addWidget(self.right_dropdown)
        right_container.addWidget(self.right_stack)
        
        right_widget = QWidget()
        right_widget.setLayout(right_container)

        self.videoPlayersLayout.setContentsMargins(0, 10, 0, 10)
        self.videoPlayersLayout.addWidget(left_widget, stretch=1)
        self.videoPlayersLayout.addWidget(right_widget, stretch=1)

    def _setup_ui_and_connections(self):
        self.projectPathLabel.setText(f"Current Project: {self.project_data.get('full_path')}")
        self.poseButton.setEnabled(False)
        self.logOutput.setReadOnly(True)

        self.importButton.setCursor(Qt.PointingHandCursor)
        self.removeButton.setCursor(Qt.PointingHandCursor)
        self.poseButton.setCursor(Qt.PointingHandCursor)

        self.importListWidget.setIconSize(QSize(128, 128))
        self.importListWidget.setResizeMode(QListWidget.Adjust)
        self.importListWidget.setViewMode(QListWidget.IconMode)
        self.importListWidget.setMovement(QListWidget.Static)
        self.importListWidget.setSelectionMode(QListWidget.ExtendedSelection)

        self.importButton.clicked.connect(self.import_files)
        self.removeButton.clicked.connect(self.remove_selected_files)
        self.poseButton.clicked.connect(self.start_pose_estimation)
        self.importListWidget.itemSelectionChanged.connect(self.update_selection)
        self.resultsListWidget.itemSelectionChanged.connect(self.on_result_selected)
        
        if self.deleteRunButton:
            self.deleteRunButton.setEnabled(False)
            self.deleteRunButton.clicked.connect(self.delete_selected_run)
            
        if self.exportFrameButton:
            self.exportFrameButton.setText("📸 Export Frame")
            self.exportFrameButton.clicked.connect(self.export_current_frame)
            
        if self.browseFolderButton:
            self.browseFolderButton.clicked.connect(self.browse_folder)
            
        if self.syncCloudButton:
            self.syncCloudButton.clicked.connect(self.start_cloud_sync)
            if not self.user_data:
                self.syncCloudButton.setEnabled(False)
                self.syncCloudButton.setText("Sync (Login Required)")
                self.syncCloudButton.setStyleSheet("background-color: #A0AEC0; color: white;")
            
        self.masterSlider.sliderMoved.connect(self.on_master_slider_moved)
        self.syncPlayButton.clicked.connect(self.toggle_play_all)
        self.rewindButton.clicked.connect(self.rewind_to_start)
        
        self.set_visualize_controls_enabled(False)
        
    def set_visualize_controls_enabled(self, enabled):
        if self.exportFrameButton: self.exportFrameButton.setEnabled(enabled)
        if self.syncPlayButton: self.syncPlayButton.setEnabled(enabled)
        if self.rewindButton: self.rewindButton.setEnabled(enabled)
        if self.masterSlider: self.masterSlider.setEnabled(enabled)
        if self.deleteRunButton: self.deleteRunButton.setEnabled(enabled)
        self.left_dropdown.setEnabled(enabled)
        self.right_dropdown.setEnabled(enabled)

    def cleanup_for_exit(self):
        self.pause_playback()
        self.left_video_player.cleanup()
        self.left_skeleton_player.cleanup()
        self.right_video_player.cleanup()
        self.right_skeleton_player.cleanup()
        
        if self.worker_thread and self.worker_thread.isRunning():
            if self.pose_worker: self.pose_worker.stop()
            self.worker_thread.quit()
            self.worker_thread.wait()

    def return_to_welcome(self):
        self._is_closing = True # Skips the exit prompt
        self.cleanup_for_exit()
        from welcome_window import WelcomeWindow
        self.welcome_win = WelcomeWindow(app_root=self.app_root, projects_root=self.projects_root)
        self.welcome_win.user_data = self.user_data
        if self.user_data and hasattr(self.welcome_win, 'loginButton') and self.welcome_win.loginButton:
            self.welcome_win.loginButton.setText("Synced ✓")
            self.welcome_win.loginButton.setEnabled(False)
        self.welcome_win.show()
        self.close()

    def sign_out(self):
        self._is_closing = True # Skips the exit prompt
        self.cleanup_for_exit()
        self.user_data = None
        from welcome_window import WelcomeWindow
        self.welcome_win = WelcomeWindow(app_root=self.app_root, projects_root=self.projects_root)
        self.welcome_win.show()
        self.close()

    def browse_folder(self):
        folder_path = self.project_data['full_path']
        if os.path.exists(folder_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))
        else:
            self.logOutput.appendPlainText("Error: Project directory not found on disk.")

    def delete_selected_run(self):
        selected_items = self.resultsListWidget.selectedItems()
        if not selected_items: return

        reply = QMessageBox.question(
            self, 'Delete Run', 
            "Are you sure you want to permanently delete this entire output run?\n\nThis will delete the 2D overlay video, and its associated .csv and .npy files.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.No: return

        self.pause_playback()
        self.left_video_player.cleanup()
        self.left_skeleton_player.cleanup()
        self.right_video_player.cleanup()
        self.right_skeleton_player.cleanup()

        out_path = selected_items[0].data(Qt.UserRole)
        filename = os.path.basename(out_path)
        
        match = re.match(r'^(?:2D|3D)_(.+?_[\d-]{10}_[\d-]{8})', filename)
        if match:
            base_identifier = match.group(1)
            deleted_count = 0
            for file in os.listdir(self.output_folder):
                if base_identifier in file:
                    file_to_delete = os.path.join(self.output_folder, file)
                    try:
                        os.remove(file_to_delete)
                        deleted_count += 1
                    except Exception as e:
                        self.logOutput.appendPlainText(f"Failed to delete {file}: {e}")
            
            self.logOutput.appendPlainText(f"Deleted {deleted_count} files associated with run: {base_identifier}")
        else:
            try:
                os.remove(out_path)
                self.logOutput.appendPlainText(f"Deleted selected file: {filename}")
            except Exception as e:
                self.logOutput.appendPlainText(f"Failed to delete {filename}: {e}")

        self.populate_output_list()
        self.set_visualize_controls_enabled(False)

    def update_player_content(self, selection, video_player, skeleton_player, stack):
        if selection == "3D Skeleton":
            stack.setCurrentWidget(skeleton_player)
            if self.current_paths['3D Skeleton'] and os.path.exists(self.current_paths['3D Skeleton']):
                skeleton_player.load_media(self.current_paths['3D Skeleton'], self.current_paths['rig_data'])
                skeleton_player.frame_rate = self.master_fps
                skeleton_player.set_position(self.masterSlider.value())
            else:
                skeleton_player.cleanup()
                skeleton_player.placeholder_label.setText("No 3D skeleton data found for this run.")
        else:
            stack.setCurrentWidget(video_player)
            path = self.current_paths[selection]
            if path and os.path.exists(path):
                video_player.load_media(path)
                video_player.set_position(self.masterSlider.value())
            else:
                video_player.cleanup()
                video_player.media_label.setText(f"{selection} not found.")

    def on_left_dropdown_changed(self, text):
        self.pause_playback()
        self.update_dropdown_states()
        self.update_player_content(text, self.left_video_player, self.left_skeleton_player, self.left_stack)

    def on_right_dropdown_changed(self, text):
        self.pause_playback()
        self.update_dropdown_states()
        self.update_player_content(text, self.right_video_player, self.right_skeleton_player, self.right_stack)
        
    def update_dropdown_states(self):
        left_text = self.left_dropdown.currentText()
        right_text = self.right_dropdown.currentText()
        
        for i in range(self.left_dropdown.count()):
            self.left_dropdown.model().item(i).setEnabled(True)
            self.right_dropdown.model().item(i).setEnabled(True)
            
        left_idx = self.right_dropdown.findText(left_text)
        if left_idx >= 0: self.right_dropdown.model().item(left_idx).setEnabled(False)
        
        right_idx = self.left_dropdown.findText(right_text)
        if right_idx >= 0: self.left_dropdown.model().item(right_idx).setEnabled(False)

    def populate_import_list(self):
        self.importListWidget.clear()
        if os.path.exists(self.input_folder):
            for filename in sorted(os.listdir(self.input_folder)):
                file_path = os.path.join(self.input_folder, filename)
                if os.path.isdir(file_path): continue 
                thumbnail = self.get_thumbnail(file_path)
                item = QListWidgetItem(QIcon(thumbnail), filename) if thumbnail else QListWidgetItem(filename)
                item.setData(Qt.UserRole, file_path)
                self.importListWidget.addItem(item)

    def populate_output_list(self):
        self.resultsListWidget.clear()
        if os.path.exists(self.output_folder):
            for filename in sorted(os.listdir(self.output_folder)):
                file_path = os.path.join(self.output_folder, filename)
                if os.path.isdir(file_path): continue
                if filename.endswith('.csv') or filename.endswith('.npy'): continue
                    
                thumbnail = self.get_thumbnail(file_path)
                item = QListWidgetItem(QIcon(thumbnail), filename) if thumbnail else QListWidgetItem("🎥 " + filename)
                item.setData(Qt.UserRole, file_path)
                self.resultsListWidget.addItem(item)

    def on_result_selected(self):
        self.pause_playback()

        selected_items = self.resultsListWidget.selectedItems()
        if not selected_items:
            self.left_video_player.cleanup()
            self.left_skeleton_player.cleanup()
            self.right_video_player.cleanup()
            self.right_skeleton_player.cleanup()
            self.set_visualize_controls_enabled(False)
            return

        out_path = selected_items[0].data(Qt.UserRole)
        filename = os.path.basename(out_path)
        
        self.current_paths['2D Overlay'] = out_path
        self.current_paths['Original'] = None
        self.current_paths['3D Skeleton'] = None
        
        match = re.match(r'^(?:2D|3D)_(.+?)_\d{4}-\d{2}-\d{2}', filename)
        if match:
            base_name = match.group(1)
            input_candidates = glob.glob(os.path.join(self.input_folder, f"{base_name}.*"))
            if input_candidates:
                self.current_paths['Original'] = input_candidates[0]

        dir_name = os.path.dirname(out_path)
        base_file = filename.replace('_overlay.mp4', '.npy')
        npy_filename = base_file.replace('2D_', '3D_')
        npy_path = os.path.join(dir_name, npy_filename)
        
        if os.path.exists(npy_path):
            self.current_paths['3D Skeleton'] = npy_path

        self.update_player_content(self.left_dropdown.currentText(), self.left_video_player, self.left_skeleton_player, self.left_stack)
        self.update_player_content(self.right_dropdown.currentText(), self.right_video_player, self.right_skeleton_player, self.right_stack)
        self.update_dropdown_states()

        ref_player = self.left_video_player if self.current_paths['Original'] else self.right_video_player
        max_frames = ref_player.total_frames
        
        self.masterSlider.setRange(0, max(0, max_frames - 1))
        self.masterSlider.setValue(0)
        
        self.master_fps = ref_player.frame_rate if ref_player.frame_rate > 0 else 30
        self.update_master_time_label(0)
        
        self.set_visualize_controls_enabled(True)

    def toggle_play_all(self):
        if self.is_playing:
            self.pause_playback()
        else:
            self.is_playing = True
            self.syncPlayButton.setText("⏸ Pause")
            self.sync_timer.start(int(1000 / self.master_fps))

    def pause_playback(self):
        self.is_playing = False
        self.sync_timer.stop()
        if hasattr(self, 'syncPlayButton') and self.syncPlayButton: 
            self.syncPlayButton.setText("▶ Play")

    def rewind_to_start(self):
        self.pause_playback()
        self.masterSlider.setValue(0)
        self.on_master_slider_moved(0)

    def on_master_slider_moved(self, position):
        if self.left_stack.currentWidget() == self.left_video_player: self.left_video_player.set_position(position)
        else: self.left_skeleton_player.set_position(position)
        
        if self.right_stack.currentWidget() == self.right_video_player: self.right_video_player.set_position(position)
        else: self.right_skeleton_player.set_position(position)
            
        self.update_master_time_label(position)

    def sync_next_frame(self):
        curr = self.masterSlider.value()
        if curr >= self.masterSlider.maximum():
            self.pause_playback()
            return
            
        next_pos = curr + 1
        
        if self.left_stack.currentWidget() == self.left_video_player: self.left_video_player.next_frame()
        else: self.left_skeleton_player.set_position(next_pos) 
        
        if self.right_stack.currentWidget() == self.right_video_player: self.right_video_player.next_frame()
        else: self.right_skeleton_player.set_position(next_pos) 
            
        self.masterSlider.blockSignals(True)
        self.masterSlider.setValue(next_pos)
        self.masterSlider.blockSignals(False)
        self.update_master_time_label(next_pos)

    def update_master_time_label(self, current_frame):
        total_frames = self.masterSlider.maximum() + 1
        if self.master_fps > 0 and total_frames > 1:
            c_sec = int(current_frame / self.master_fps)
            t_sec = int(total_frames / self.master_fps)
            self.masterTimeLabel.setText(f"{c_sec // 60:02d}:{c_sec % 60:02d} / {t_sec // 60:02d}:{t_sec % 60:02d}")
        else:
            self.masterTimeLabel.setText("Image")

    # --- Advanced Frame Export Logic ---
    def _stitch_images(self, img1: QImage, img2: QImage) -> QImage:
        """Helper function to mathematically stitch two QImages side by side"""
        if not img1: return img2
        if not img2: return img1
        
        # Scale them so their heights match perfectly
        h = max(img1.height(), img2.height())
        img1 = img1.scaledToHeight(h, Qt.SmoothTransformation)
        img2 = img2.scaledToHeight(h, Qt.SmoothTransformation)
        
        w = img1.width() + img2.width()
        result = QImage(w, h, QImage.Format_ARGB32)
        result.fill(Qt.white) # White background buffer
        
        painter = QPainter(result)
        painter.drawImage(0, 0, img1)
        painter.drawImage(img1.width(), 0, img2)
        painter.end()
        return result

    def export_current_frame(self):
        self.pause_playback()
        dialog = ExportDialog(self)
        if not dialog.exec() or not dialog.choice:
            return
            
        choice = dialog.choice
        current_frame = self.masterSlider.value()
        
        # Build a smart default filename
        base_name = "project"
        if self.current_paths['Original']:
            base_name = os.path.splitext(os.path.basename(self.current_paths['Original']))[0]
            
        default_name = f"{base_name}_{choice}_export_frame_{current_frame}.png"
        
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Frame", default_name, "PNG Image (*.png);;JPEG Image (*.jpg)")
        
        if not save_path: return
        
        img_left = None
        img_right = None
        
        # Pull left image
        if choice in ["left", "both"]:
            active_left = self.left_skeleton_player if self.left_stack.currentWidget() == self.left_skeleton_player else self.left_video_player
            img_left = active_left.get_current_frame_image()
            
        # Pull right image
        if choice in ["right", "both"]:
            active_right = self.right_skeleton_player if self.right_stack.currentWidget() == self.right_skeleton_player else self.right_video_player
            img_right = active_right.get_current_frame_image()
            
        # Assemble final image
        final_img = None
        if choice == "left": final_img = img_left
        elif choice == "right": final_img = img_right
        elif choice == "both":
            final_img = self._stitch_images(img_left, img_right)
            
        if final_img:
            final_img.save(save_path)
            self.logOutput.appendPlainText(f"Success! Exported frame saved to: {save_path}")
        else:
            self.logOutput.appendPlainText("Error: Could not extract frame to export.")

    def get_thumbnail(self, file_path):
        pixmap = QPixmap()
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg']:
            pixmap.load(file_path)
        elif ext in ['.mp4', '.avi', '.mov']:
            cap = cv2.VideoCapture(file_path)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    height, width, channel = frame.shape
                    bytes_per_line = 3 * width
                    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(q_image)
                cap.release()
        return pixmap.scaled(QSize(128, 128), Qt.KeepAspectRatio, Qt.SmoothTransformation) if not pixmap.isNull() else None

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()

    def dropEvent(self, event):
        if self.importListWidget.geometry().contains(event.position().toPoint()):
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
                valid_extensions = ['.mp4', '.avi', '.mov', '.png', '.jpg', '.jpeg']
                file_paths = [url.toLocalFile() for url in event.mimeData().urls() if os.path.splitext(url.toLocalFile())[1].lower() in valid_extensions]
                if file_paths: self.copy_files_to_project(file_paths)

    def import_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Import Media", "", "Video and Image Files (*.mp4 *.avi *.mov *.png *.jpg *.jpeg)")
        if file_paths:
            self.copy_files_to_project(file_paths)

    def copy_files_to_project(self, file_paths):
        for src_path in file_paths:
            if os.path.isfile(src_path):
                shutil.copy2(src_path, os.path.join(self.input_folder, os.path.basename(src_path)))
        self.populate_import_list()

    def remove_selected_files(self):
        for item in self.importListWidget.selectedItems():
            file_path = item.data(Qt.UserRole)
            try:
                if os.path.exists(file_path): os.remove(file_path)
                self.importListWidget.takeItem(self.importListWidget.row(item))
            except Exception as e:
                self.logOutput.appendPlainText(f"Error removing file: {e}")
        self.populate_import_list()

    def update_selection(self):
        selected_items = self.importListWidget.selectedItems()
        num_selected = len(selected_items)
        if num_selected == 0:
            self.inputChosenLabel.setText("Input Chosen: None")
            self.poseButton.setEnabled(False)
            return
        is_video = any(item.data(Qt.UserRole).lower().endswith(('.mp4', '.avi', '.mov')) for item in selected_items)
        if (is_video and num_selected > 1) or (is_video and any(not item.data(Qt.UserRole).lower().endswith(('.mp4', '.avi', '.mov')) for item in selected_items)):
            self.inputChosenLabel.setText("Error: Invalid selection")
            self.poseButton.setEnabled(False)
        else:
            self.inputChosenLabel.setText(f"Input Chosen: {num_selected} item(s)")
            self.poseButton.setEnabled(True)

    def start_pose_estimation(self):
        selected_items = self.importListWidget.selectedItems()
        if not selected_items: return
        
        selected_mode = "2D" if "2D" in self.modeComboBox.currentText() else "3D"
        
        self.logOutput.clear()
        self.set_ui_enabled(False)
        media_paths = [item.data(Qt.UserRole) for item in selected_items]
        
        self.worker_thread = QThread()
        self.pose_worker = PoseWorker(
            media_paths=media_paths,
            dlc_model_path=self.dlc_model_path,
            project_input_path=self.project_data['full_path'] + '/input',
            project_output_path=self.project_data['full_path'] + '/output',
            mode=selected_mode
        )
        self.pose_worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.pose_worker.run_analysis)
        self.pose_worker.progress.connect(self.logOutput.appendPlainText)
        self.pose_worker.finished.connect(self.on_analysis_finished)
        self.worker_thread.start()

    def on_analysis_finished(self, message):
        self.logOutput.appendPlainText(f"\n{message}")
        self.set_ui_enabled(True)
        self.populate_output_list()
        
        if self.resultsListWidget.count() > 0:
            self.resultsListWidget.setCurrentRow(self.resultsListWidget.count() - 1)
            
        self.worker_thread.quit()
        self.worker_thread.wait()
        self.worker_thread = None
        self.pose_worker = None

    def start_cloud_sync(self):
        if hasattr(self, 'syncCloudButton') and self.syncCloudButton:
            self.syncCloudButton.setEnabled(False)
            self.syncCloudButton.setText("Syncing...")
            
        self.sync_action.setEnabled(False)
        self.logOutput.clear()
        self.sync_worker_thread = QThread()
        self.sync_worker = SyncWorker(self.user_data, self.project_data)
        self.sync_worker.moveToThread(self.sync_worker_thread)
        self.sync_worker_thread.started.connect(self.sync_worker.run_sync)
        self.sync_worker.progress.connect(self.logOutput.appendPlainText)
        self.sync_worker.finished.connect(self.on_sync_finished)
        self.sync_worker_thread.start()

    def on_sync_finished(self, message):
        self.logOutput.appendPlainText(f"\n{message}")
        self.sync_action.setEnabled(True)
        
        if hasattr(self, 'syncCloudButton') and self.syncCloudButton:
            self.syncCloudButton.setEnabled(True)
            self.syncCloudButton.setText("☁️ Sync to Cloud")
            
        self.sync_worker_thread.quit()
        self.sync_worker_thread.wait()
        
        # If this sync was triggered by the user closing the app
        if getattr(self, 'exit_after_sync', False):
            self._is_closing = True
            self.close()

    def set_ui_enabled(self, enabled):
        self.importListWidget.setEnabled(enabled)
        self.resultsListWidget.setEnabled(enabled)
        self.modeComboBox.setEnabled(enabled)
        self.importButton.setEnabled(enabled)
        self.removeButton.setEnabled(enabled)
        self.poseButton.setEnabled(enabled)
        self.menu_bar.setEnabled(enabled)

    def create_new_project_from_menu(self):
        dialog = NewProjectDialog(self, projects_root=self.projects_root)
        if dialog.exec():
            project_data = dialog.get_project_data()
            full_project_path = os.path.join(self.projects_root, project_data['name'])
            try:
                os.makedirs(os.path.join(full_project_path, 'input'), exist_ok=True)
                os.makedirs(os.path.join(full_project_path, 'output'), exist_ok=True)
                project_data['full_path'] = full_project_path
                self.new_main_win = MainWindow(project_data, self.app_root, self.projects_root, self.user_data)
                self.new_main_win.show()
                self.close()
            except OSError as e:
                self.logOutput.appendPlainText(f"Error creating directory: {e}")

    def open_existing_project_from_menu(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Project Folder", self.projects_root)
        if directory:
            project_data = {"name": os.path.basename(directory), "full_path": directory}
            self.new_main_win = MainWindow(project_data, self.app_root, self.projects_root, self.user_data)
            self.new_main_win.show()
            self.close()