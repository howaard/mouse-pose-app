import os
import requests
import datetime
from PySide6.QtCore import QObject, Signal, Slot

class SyncWorker(QObject):
    progress = Signal(str)
    finished = Signal(str)

    def __init__(self, user_data, project_data):
        super().__init__()
        self.user_data = user_data
        self.project_data = project_data
        self.is_running = True
        self.base_url = "https://mouse-pose.com"

    @Slot()
    def run_sync(self):
        try:
            if not self.user_data or 'id' not in self.user_data:
                self.finished.emit("Error: You must be logged in to sync to the cloud.")
                return

            self.progress.emit(f"\n--- Starting Cloud Sync for '{self.project_data['name']}' ---")
            project_path = self.project_data['full_path']
            input_folder = os.path.join(project_path, 'input')
            output_folder = os.path.join(project_path, 'output')

            # --- Persistent Project ID to prevent web duplicates ---
            id_file_path = os.path.join(project_path, '.cloud_id')
            project_id = None
            
            if os.path.exists(id_file_path):
                with open(id_file_path, 'r') as f:
                    project_id = f.read().strip()
            
            if not project_id:
                project_id = str(int(datetime.datetime.now().timestamp()))
                with open(id_file_path, 'w') as f:
                    f.write(project_id)

            files_to_upload = []
            valid_extensions = ('.mp4', '.avi', '.mov', '.csv')

            def scan_folder(folder_path, folder_label):
                if not os.path.exists(folder_path): return
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if file.lower().endswith(valid_extensions):
                            files_to_upload.append({
                                "local_path": os.path.join(root, file),
                                "folder_label": folder_label
                            })

            scan_folder(input_folder, "input")
            scan_folder(output_folder, "output")

            if not files_to_upload:
                self.finished.emit("No valid media or data files found to sync.")
                return

            input_files_data = []
            output_files_data = []

            for i, item in enumerate(files_to_upload):
                if not self.is_running: break
                
                file_path = item["local_path"]
                folder_label = item["folder_label"]
                file_name = os.path.basename(file_path)
                
                file_size_bytes = os.path.getsize(file_path)
                file_size_mb = file_size_bytes / (1024 * 1024)
                size_str = f"{file_size_mb:.1f} MB" if file_size_mb >= 1 else f"{file_size_bytes / 1024:.1f} KB"
                
                file_ext = file_path.lower().split('.')[-1]
                if file_ext in ['mp4', 'avi', 'mov']:
                    content_type = "video/mp4"
                    category = "video"
                else:
                    content_type = "text/csv"
                    category = "data"

                # 1. Ask Next.js for a temporary AWS S3 upload link
                self.progress.emit(f"[{i+1}/{len(files_to_upload)}] Requesting secure link for {file_name}...")
                res = requests.post(f"{self.base_url}/api/upload", json={
                    "filename": file_name,
                    "contentType": content_type
                }, timeout=10)
                res.raise_for_status()
                
                urls = res.json()
                presigned_url = urls.get("presignedUrl")
                file_url = urls.get("fileUrl")

                # 2. Upload directly to AWS S3 (AWS automatically overwrites if file exists)
                self.progress.emit(f"[{i+1}/{len(files_to_upload)}] Uploading/Replacing {file_name} to AWS ({size_str})...")
                with open(file_path, 'rb') as f:
                    upload_res = requests.put(presigned_url, data=f, headers={"Content-Type": content_type})
                    upload_res.raise_for_status()

                # 3. Save the public S3 URL and file metadata
                file_info = {
                    "name": file_name, 
                    "size": size_str, 
                    "url": file_url,
                    "category": category
                }
                
                if folder_label == "input":
                    input_files_data.append(file_info)
                else:
                    output_files_data.append(file_info)

            if not self.is_running:
                self.finished.emit("Sync cancelled by user.")
                return

            # 4. Save the cleanly categorized Project Metadata to MongoDB
            self.progress.emit("Saving project metadata to database...")
            project_payload = {
                "id": project_id, 
                "name": self.project_data['name'],
                "date": datetime.datetime.now().strftime('%Y-%m-%d'),
                "input_files": input_files_data,
                "output_files": output_files_data
            }

            sync_res = requests.post(f"{self.base_url}/api/projects/sync", json={
                "userId": self.user_data['id'],
                "project": project_payload
            }, timeout=10)
            sync_res.raise_for_status()

            self.finished.emit("✅ Sync Complete! Project data updated and uploaded.")

        except requests.exceptions.RequestException as e:
            self.finished.emit(f"❌ Network Error during sync: {str(e)}")
        except Exception as e:
            self.finished.emit(f"❌ Error during sync: {str(e)}")

    def stop(self):
        self.is_running = False