import sys
import os
from PySide6.QtWidgets import QApplication
from welcome_window import WelcomeWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # --- Determine Core Application Paths ---
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    PROJECTS_ROOT = os.path.join(APP_ROOT, "projects")
    DLC_MODEL_ROOT = os.path.join(APP_ROOT, "deeplabcut")

    # --- Create Essential Folders if they don't exist ---
    if not os.path.exists(PROJECTS_ROOT):
        os.makedirs(PROJECTS_ROOT)
        print(f"Created 'projects' directory at: {PROJECTS_ROOT}")
        
    if not os.path.exists(DLC_MODEL_ROOT):
        os.makedirs(DLC_MODEL_ROOT)
        print(f"Created 'deeplabcut' directory at: {DLC_MODEL_ROOT}")

    # Pass paths to the welcome window.
    window = WelcomeWindow(app_root=APP_ROOT, projects_root=PROJECTS_ROOT)
    
    window.show()
    sys.exit(app.exec())