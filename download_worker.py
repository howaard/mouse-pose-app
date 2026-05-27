import os
import requests
import json
from PySide6.QtCore import QObject, Signal, Slot

class DownloadWorker(QObject):
    progress_update = Signal(str)
    finished = Signal(bool, str, dict) # Success status, message, local project data

    def __init__(self, cloud_project, projects_root):
        super().__init__()
        self.cloud_project = cloud_project
        self.projects_root = projects_root
        self.is_running = True

    @Slot()
    def run_download(self):
        try:
            project_name = self.cloud_project['name']
            
            # Ensure safe folder name
            safe_folder_name = "".join([c for c in project_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            local_project_path = os.path.join(self.projects_root, safe_folder_name)
            
            # Create local directories
            input_folder = os.path.join(local_project_path, 'input')
            output_folder = os.path.join(local_project_path, 'output')
            os.makedirs(input_folder, exist_ok=True)
            os.makedirs(output_folder, exist_ok=True)

            all_files = []
            for f in self.cloud_project.get('input_files', []):
                all_files.append((f, input_folder))
            for f in self.cloud_project.get('output_files', []):
                all_files.append((f, output_folder))

            if not all_files:
                self.finished.emit(False, "No files found in cloud project.", {})
                return

            sync_history = {"project_id": self.cloud_project['id'], "files": {}}
            
            for i, (file_data, target_folder) in enumerate(all_files):
                if not self.is_running: break
                
                file_name = file_data['name']
                file_url = file_data['url']
                local_file_path = os.path.join(target_folder, file_name)
                
                self.progress_update.emit(f"Downloading {file_name}... ({i+1}/{len(all_files)})")
                
                # Stream the download so we don't consume all RAM for huge videos
                with requests.get(file_url, stream=True, timeout=15) as r:
                    r.raise_for_status()
                    with open(local_file_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if not self.is_running: break
                            f.write(chunk)
                            
                # Save to history so it doesn't re-upload immediately if synced
                if self.is_running:
                    folder_label = "input" if target_folder == input_folder else "output"
                    file_key = f"{folder_label}/{file_name}"
                    sync_history["files"][file_key] = {
                        "size": os.path.getsize(local_file_path),
                        "mtime": os.path.getmtime(local_file_path),
                        "url": file_url
                    }

            if not self.is_running:
                self.finished.emit(False, "Download cancelled.", {})
                return

            # Save the sync cache locally
            with open(os.path.join(local_project_path, '.sync_history.json'), 'w') as f:
                json.dump(sync_history, f)

            local_project_data = {"name": safe_folder_name, "full_path": local_project_path}
            self.finished.emit(True, "Download complete!", local_project_data)

        except Exception as e:
            self.finished.emit(False, str(e), {})

    def stop(self):
        self.is_running = False