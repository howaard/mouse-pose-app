import os
import json
import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy, QStackedWidget, QFileDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class SkeletonPlayer(QWidget):
    """A dumb, display-only 3D canvas screen. Controlled entirely by the Main Window."""
    def __init__(self, title="3D Skeleton Visualizer"):
        super().__init__()
        self.predicted_poses = None
        self.joint_names = []
        self.skeleton_bones = []
        self.total_frames = 0
        
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2D3748;")
        
        self.stacked_widget = QStackedWidget()
        
        self.placeholder_label = QLabel("Toggle to '3D Skeleton' to view spatial data.")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.placeholder_label.setMinimumHeight(450)
        self.placeholder_label.setStyleSheet("background-color: #1A202C; border: 1px solid #CBD5E0; border-radius: 8px; color: #A0AEC0; font-size: 14px; font-style: italic;")

        self.figure = Figure(facecolor='#1A202C')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("border-radius: 8px;")
        
        self.ax = self.figure.add_subplot(111, projection='3d')
        self.ax.set_facecolor('#1A202C')
        
        # Disable axes mapping for a clean WebGL look
        self.ax.axis('off')
        self.figure.subplots_adjust(left=0, right=1, bottom=0, top=1)

        self.stacked_widget.addWidget(self.placeholder_label)
        self.stacked_widget.addWidget(self.canvas)
        self.stacked_widget.setCurrentWidget(self.placeholder_label)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.title_label)
        layout.addWidget(self.stacked_widget, stretch=1)
        self.setLayout(layout)

    def cleanup(self):
        self.predicted_poses = None
        self.total_frames = 0
        self.stacked_widget.setCurrentWidget(self.placeholder_label)

    def load_media(self, npy_path, rig_json_path):
        self.cleanup()
        
        if not os.path.exists(npy_path) or not os.path.exists(rig_json_path):
            self.placeholder_label.setText("Required 3D data files not found.")
            return

        with open(rig_json_path, 'r') as f:
            rig_data = json.load(f)
            self.joint_names = rig_data.get('processing_order', [])
            self.skeleton_bones = rig_data.get('kinematic_chain', [])

        self.predicted_poses = np.load(npy_path)
        self.total_frames = len(self.predicted_poses)

        self.ax.clear()
        self.ax.axis('off')

        all_x = self.predicted_poses[..., 0]
        all_y = self.predicted_poses[..., 1]
        all_z = self.predicted_poses[..., 2]

        self.ax.set_xlim(np.min(all_x), np.max(all_x))
        self.ax.set_ylim(np.min(all_y), np.max(all_y))
        self.ax.set_zlim(np.min(all_z), np.max(all_z))
        
        # Forces plotting bounds to act like a perfect cube
        self.ax.set_box_aspect(aspect=(1,1,1))

        # Desktop Theme Colors
        self.scatter = self.ax.scatter([], [], [], c='#00B5AD', s=15, alpha=0.8)
        self.lines = [self.ax.plot([], [], [], c='#805AD5', lw=2)[0] for _ in self.skeleton_bones]

        self.stacked_widget.setCurrentWidget(self.canvas)
        self.set_position(0)

    def set_position(self, position):
        if self.predicted_poses is None or position >= self.total_frames: return
        pose = self.predicted_poses[position]
        
        self.scatter._offsets3d = (pose[:, 0], pose[:, 1], pose[:, 2])
        for i, (parent, child) in enumerate(self.skeleton_bones):
            p_idx = self.joint_names.index(parent)
            c_idx = self.joint_names.index(child)
            self.lines[i].set_data_3d([pose[p_idx, 0], pose[c_idx, 0]], [pose[p_idx, 1], pose[c_idx, 1]], [pose[p_idx, 2], pose[c_idx, 2]])
            
        self.canvas.draw_idle()

    # Used by the custom Export Dialog to extract the raw canvas into memory
    def get_current_frame_image(self):
        if self.predicted_poses is None: return None
        self.canvas.draw()
        buf = self.canvas.buffer_rgba()
        w, h = self.canvas.get_width_height()
        qimg = QImage(buf, w, h, QImage.Format_RGBA8888)
        return qimg.copy()

    def export_current_frame(self, default_filename="3d_skeleton_frame.png"):
        img = self.get_current_frame_image()
        if img:
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Frame", default_filename, "PNG Image (*.png);;JPEG Image (*.jpg)")
            if save_path: img.save(save_path)