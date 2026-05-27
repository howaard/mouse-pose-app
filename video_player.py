import cv2
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFileDialog, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage

class VideoPlayer(QWidget):
    """A dumb, display-only video screen. Controlled entirely by the Main Window."""
    def __init__(self, title=""):
        super().__init__()
        self.video_path = None
        self.capture = None
        self.frame_rate = 30
        self.total_frames = 0
        self.is_image = False

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2D3748;")
        
        self.media_label = QLabel("Select a file to preview.")
        self.media_label.setAlignment(Qt.AlignCenter)
        
        # Expanding + Minimum Size (1,1) prevents zooming but correctly fills the layout space
        self.media_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.media_label.setMinimumSize(1, 1) 
        
        self.media_label.setStyleSheet("background-color: #1A202C; border: 1px solid #CBD5E0; border-radius: 8px; color: #A0AEC0; font-size: 14px; font-style: italic;")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.title_label)
        layout.addWidget(self.media_label, stretch=1)
        self.setLayout(layout)

    def load_media(self, path):
        self.cleanup()
        self.video_path = path
        
        if path.lower().endswith(('.png', '.jpg', '.jpeg')):
            self.is_image = True
            self.total_frames = 1
            pixmap = QPixmap(path)
            self.media_label.setPixmap(pixmap.scaled(self.media_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.is_image = False
            self.capture = cv2.VideoCapture(path)
            if self.capture.isOpened():
                self.frame_rate = self.capture.get(cv2.CAP_PROP_FPS)
                self.total_frames = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
                self.set_position(0)
            else:
                self.media_label.setText("Error loading video.")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.is_image and self.video_path:
            pixmap = QPixmap(self.video_path)
            self.media_label.setPixmap(pixmap.scaled(self.media_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        elif not self.is_image and self.capture and self.capture.isOpened():
            current_pos = int(self.capture.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            self.set_position(max(0, current_pos))

    def cleanup(self):
        if self.capture:
            self.capture.release()
            self.capture = None
        self.media_label.clear()
        self.media_label.setText("Select a file to preview.")
        self.video_path = None
        self.total_frames = 0
        self.is_image = False

    def display_frame_from_data(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.media_label.setPixmap(pixmap.scaled(self.media_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def next_frame(self):
        if self.is_image: return
        if self.capture and self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret: self.display_frame_from_data(frame)

    def set_position(self, position):
        if self.is_image or not self.capture: return
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, position)
        ret, frame = self.capture.read()
        if ret: self.display_frame_from_data(frame)

    # Used by the custom Export Dialog to extract the raw image into memory
    def get_current_frame_image(self):
        if not self.video_path: return None
        if self.is_image:
            pixmap = self.media_label.pixmap()
            return pixmap.toImage() if pixmap else None
        else:
            current_frame_pos = int(self.capture.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            self.capture.set(cv2.CAP_PROP_POS_FRAMES, max(0, current_frame_pos))
            ret, frame = self.capture.read()
            if ret:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                q_img = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
                return q_img.copy() # Copy prevents memory corruption
        return None

    def export_current_frame(self, default_filename="frame.png"):
        img = self.get_current_frame_image()
        if img:
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Frame", default_filename, "PNG Image (*.png);;JPEG Image (*.jpg)")
            if save_path: img.save(save_path)