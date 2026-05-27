# 🐁 Monocular 3D Mouse Pose Estimation

![Python](https://img.shields.io/badge/Python-3.10-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-CUDA_11.8-EE4C2C)
![PySide6](https://img.shields.io/badge/UI-PySide6-41CD52)
![Next.js](https://img.shields.io/badge/Cloud-Next.js%20%7C%20AWS-000000)

A hybrid AI desktop application and cloud dashboard designed to extract precise 3D kinematic data from standard 2D laboratory mouse footage, eliminating the need for expensive multi-camera motion capture rigs.

---

## ✨ Core Features
* **Custom Spatio-Temporal 3D AI:** Leverages a custom PyTorch Transformer with NetworkX spatial graph bias to mathematically infer 3D depth from flat 2D projections.
* **Dual-Pane Synchronized UI:** Built with PySide6, featuring a custom `QTimer` master clock for frame-perfect playback between raw OpenCV video and 3D Matplotlib skeletal overlays.
* **Cloud Collaboration:** Secure, out-of-band AWS S3 upload pipelines synced with a Next.js/MongoDB web dashboard for remote team collaboration.

---

## 📥 Model Weights Download
Due to file size constraints, the pre-trained RTMPose model weights are hosted externally. 
1. Download the weights here: [https://drive.google.com/drive/folders/1J8SNtwVYJroW1cTlSppY7jwjQ1Npf9fX?usp=sharing]
2. Place the downloaded `.pt` file into the following directory before running the application:
   `deeplabcut/dlc-models-pytorch/iteration-0/rtmposexAug25-trainset95shuffle1/train/`

---

## 🚀 Quick Start Installation

**1. Initialize Environment**
```bash
conda create -n mouse python=3.10.16 -y
conda activate mouse

**2. Install Hardware Acceleration (Nvidia GPU Recommended)**
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia -y

**3. Install Dependencies & Launch**
pip install -r requirements.txt
python main.py
