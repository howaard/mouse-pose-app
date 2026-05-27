import os
import re
import time
import yaml
import shutil
import glob
import cv2
import pandas as pd
import concurrent.futures
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import QObject, Signal, Slot

class PoseWorker(QObject):
    progress = Signal(str)
    finished = Signal(str)
    
    def __init__(self, media_paths, dlc_model_path, project_input_path, project_output_path, mode="2D"):
        super().__init__()
        self.media_paths = media_paths
        self.is_video = any(f.lower().endswith(('.mp4', '.avi', '.mov')) for f in media_paths)
        self.dlc_model_path = dlc_model_path
        self.project_input_path = project_input_path
        self.project_output_path = project_output_path
        self.mode = mode 
        self.is_running = True
        self.config_paths_to_backup = []

    def _backup_and_rewrite_configs(self):
        self.progress.emit("Backing up and rewriting DLC model configurations...")
        normalized_dlc_model_path = str(Path(self.dlc_model_path).resolve())
        model_base_path = os.path.join(self.dlc_model_path, "dlc-models-pytorch", "iteration-0")
        try: model_name_folder = next(d for d in os.listdir(model_base_path) if os.path.isdir(os.path.join(model_base_path, d)))
        except StopIteration: raise FileNotFoundError(f"Could not find a model folder inside {model_base_path}")

        main_config_path = os.path.join(self.dlc_model_path, "config.yaml")
        pose_cfg_path = os.path.join(model_base_path, model_name_folder, "test", "pose_cfg.yaml")
        pytorch_cfg_path = os.path.join(model_base_path, model_name_folder, "train", "pytorch_config.yaml")
        
        self.config_paths_to_backup = [main_config_path, pose_cfg_path, pytorch_cfg_path]
        for path in self.config_paths_to_backup:
            if os.path.exists(path): shutil.copyfile(path, path + ".bak")

        with open(main_config_path, 'r') as f: main_config = yaml.safe_load(f)
        main_config['project_path'] = normalized_dlc_model_path
        with open(main_config_path, 'w') as f: yaml.dump(main_config, f)

        if os.path.exists(pose_cfg_path):
            with open(pose_cfg_path, 'r') as f: pose_config = yaml.safe_load(f)
            pose_config['dataset'] = os.path.join(normalized_dlc_model_path, 'training-datasets', 'iteration-0', model_name_folder, 'CollectedData_test.csv')
            with open(pose_cfg_path, 'w') as f: yaml.dump(pose_config, f)

        if os.path.exists(pytorch_cfg_path):
            with open(pytorch_cfg_path, 'r') as f: pytorch_config = yaml.safe_load(f)
            pose_cfg_for_train_path = os.path.join(model_base_path, model_name_folder, "train", "pose_cfg.yaml")
            normalized_pose_cfg_for_train_path = str(Path(pose_cfg_for_train_path).resolve())
            pytorch_config['metadata']['project_path'] = normalized_dlc_model_path
            pytorch_config['metadata']['pose_config_path'] = normalized_pose_cfg_for_train_path
            with open(pytorch_cfg_path, 'w') as f: yaml.dump(pytorch_config, f)

        return main_config_path

    def _restore_configs(self):
        for path in self.config_paths_to_backup:
            bak_path = path + ".bak"
            if os.path.exists(bak_path): shutil.move(bak_path, path)

    def _extract_frames(self, video_path):
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        frames_folder = os.path.join(self.project_input_path, f"{video_name}_frames")
        
        self.progress.emit(f"\nExtracting frames for '{video_name}'...")
        if os.path.exists(frames_folder): shutil.rmtree(frames_folder)
        os.makedirs(frames_folder)

        if not self.is_running: return frames_folder

        cap = cv2.VideoCapture(video_path)
        count = 0
        def write_frame(filename, image): cv2.imwrite(filename, image, [cv2.IMWRITE_PNG_COMPRESSION, 1])

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            while cap.isOpened() and self.is_running:
                ret, frame = cap.read()
                if not ret: break
                frame_filename = os.path.join(frames_folder, f"frame_{count:04d}.png")
                futures.append(executor.submit(write_frame, frame_filename, frame))
                count += 1
            for _ in concurrent.futures.as_completed(futures): pass
        cap.release()
        return frames_folder

    def _run_dlc_analysis(self, config_path, image_folder):
        self.progress.emit("\nLoading DeepLabCut library...")
        import deeplabcut
        self.progress.emit(f"Starting 2D pose estimation on folder: {os.path.basename(image_folder)}")
        
        files_before_analysis = set(os.listdir(image_folder))
        deeplabcut.analyze_time_lapse_frames(config_path, image_folder, frametype='.png', save_as_csv=True)
        files_after_analysis = set(os.listdir(image_folder))

        new_files = files_after_analysis - files_before_analysis
        csv_files = [f for f in new_files if f.endswith('.csv')]
        if not csv_files: raise FileNotFoundError("DeepLabCut analysis finished but no output CSV file was found.")
        for h5_file in [f for f in new_files if f.endswith('.h5')]:
            os.remove(os.path.join(image_folder, h5_file))
        return os.path.join(image_folder, csv_files[0]) 

    def _overlay_keypoints(self, csv_path, overlay_prefix, analysis_image_folder):
        self.progress.emit(f"\nCreating keypoint overlay images from {os.path.basename(csv_path)}...")
        overlay_folder_name = f"{overlay_prefix}_overlay_frames"
        overlay_output_path = os.path.join(self.project_output_path, overlay_folder_name)
        os.makedirs(overlay_output_path, exist_ok=True)

        try:
            df = pd.read_csv(csv_path, header=[1, 2], index_col=0, skiprows=[0])
            df = df.apply(pd.to_numeric, errors='coerce')
        except Exception as e: raise ValueError(f"Error reading results CSV: {e}")

        bodyparts = df.columns.get_level_values(0).unique()
        frame_lookup = {}
        for image_ref, row in df.iterrows():
            nums = re.findall(r'\d+', str(image_ref))
            if nums: frame_lookup[int(nums[-1])] = row

        all_original_frames = sorted([f for f in os.listdir(analysis_image_folder) if f.endswith('.png')])

        def process_overlay(frame_filename, out_path):
            img_path = os.path.join(analysis_image_folder, frame_filename)
            img = cv2.imread(img_path)
            if img is None: return False
            nums = re.findall(r'\d+', frame_filename)
            if nums:
                row = frame_lookup.get(int(nums[-1]))
                if row is not None:
                    for bp in bodyparts:
                        try:
                            x, y = row.get((bp, 'x')), row.get((bp, 'y'))
                            if pd.notna(x) and pd.notna(y):
                                if (bp, 'likelihood') not in row or row[(bp, 'likelihood')] > 0.0:
                                    cv2.circle(img, (int(float(x)), int(float(y))), 5, (0, 255, 0), -1)
                        except: continue
            cv2.imwrite(out_path, img, [cv2.IMWRITE_PNG_COMPRESSION, 1])
            return True

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for frame_filename in all_original_frames:
                if not self.is_running: break
                output_save_path = os.path.join(overlay_output_path, f"{Path(frame_filename).stem}_overlay.png")
                futures.append(executor.submit(process_overlay, frame_filename, output_save_path))
            for _ in concurrent.futures.as_completed(futures): pass
        return overlay_output_path

    def _stitch_video(self, overlay_frames_folder, original_video_path, output_video_path):
        import imageio
        def read_and_convert_image(path):
            img = cv2.imread(path)
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if img is not None else None

        self.progress.emit("\nStitching and encoding overlay video (H.264)...")
        writer = None
        try:
            fps = 30.0
            if self.is_video:
                cap = cv2.VideoCapture(original_video_path)
                fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
                cap.release()

            frames = sorted([f for f in os.listdir(overlay_frames_folder) if f.endswith('.png')])
            if not frames: return

            writer = imageio.get_writer(output_video_path, fps=fps, codec='libx264', macro_block_size=None)
            chunk_size = 50
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for i in range(0, len(frames), chunk_size):
                    if not self.is_running: break
                    chunk_paths = [os.path.join(overlay_frames_folder, f) for f in frames[i:i+chunk_size]]
                    images = list(executor.map(read_and_convert_image, chunk_paths))
                    for img in images:
                        if img is not None: writer.append_data(img)

            if writer is not None: writer.close()
            self.progress.emit(f"✅ Overlay video created successfully!")
        except Exception as e:
            if writer is not None: writer.close()
            self.progress.emit(f"❌ Error creating video: {e}")

    @Slot()
    def run_analysis(self):
        analysis_image_folder = None
        try:
            self.progress.emit(f"--- Starting {self.mode} Pose Estimation Pipeline ---")
            config_path = self._backup_and_rewrite_configs()

            if self.is_video: analysis_image_folder = self._extract_frames(self.media_paths[0])
            else:
                analysis_image_folder = os.path.join(self.project_output_path, "temp_image_analysis")
                if os.path.exists(analysis_image_folder): shutil.rmtree(analysis_image_folder)
                os.makedirs(analysis_image_folder)
                for path in self.media_paths: shutil.copy(path, analysis_image_folder)

            if not self.is_running: return
            generated_csv_path = self._run_dlc_analysis(config_path, analysis_image_folder)

            if not self.is_running: return
            base_name = os.path.splitext(os.path.basename(self.media_paths[0]))[0]
            
            # --- CLEANUP / OVERWRITE OLD FILES ---
            self.progress.emit("Cleaning up older output files for this specific video...")
            old_files = glob.glob(os.path.join(self.project_output_path, f"*_{base_name}_*"))
            for old_file in old_files:
                try: os.remove(old_file)
                except: pass
            
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            new_csv_base_name = f"2D_{base_name}_{timestamp}"
            final_2d_csv_path = os.path.join(self.project_output_path, f"{new_csv_base_name}.csv")
            
            shutil.move(generated_csv_path, final_2d_csv_path)
            self.progress.emit(f"\n✅ Final 2D keypoints saved to: {os.path.basename(final_2d_csv_path)}")
            
            overlay_output_path = self._overlay_keypoints(final_2d_csv_path, new_csv_base_name, analysis_image_folder)
            if not self.is_running: return
            video_output_path = os.path.join(self.project_output_path, f"{new_csv_base_name}_overlay.mp4")
            self._stitch_video(overlay_output_path, self.media_paths[0], video_output_path)
            if os.path.exists(overlay_output_path): shutil.rmtree(overlay_output_path)

            if self.mode == "3D" and self.is_running:
                self.progress.emit("\n--- Handing off to 3D Inference Engine ---")
                try:
                    app_root = os.path.dirname(self.dlc_model_path)
                    models_folder = os.path.join(app_root, "models")
                    from engine_3d import run_3d_pipeline
                    run_3d_pipeline(
                        input_2d_csv_path=final_2d_csv_path,
                        output_folder=self.project_output_path,
                        models_folder=models_folder,
                        progress_callback=self.progress.emit,
                        is_running_func=lambda: self.is_running
                    )
                except Exception as e:
                    import traceback
                    self.progress.emit(f"\n❌ 3D Inference Failed: {str(e)}")
                    self.progress.emit(traceback.format_exc())

            if self.is_running:
                self.finished.emit(f"✅ Successfully completed {self.mode} processing for {os.path.basename(self.media_paths[0])}.")

        except Exception as e:
            if self.is_running:
                import traceback
                self.finished.emit(f"\n--- ERROR --- \n{e}\n{traceback.format_exc()}\n-------------")
        
        finally:
            self._restore_configs()
            if not self.is_video and analysis_image_folder and "temp_image_analysis" in analysis_image_folder:
                if os.path.exists(analysis_image_folder): shutil.rmtree(analysis_image_folder)
            
    def stop(self):
        self.progress.emit("Stopping analysis... Please wait for processes to safely terminate.")
        self.is_running = False