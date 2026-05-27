1. Create a new conda environment: 
conda create -n mouse python=3.10.16
conda activate mouse

2. Install PyTorch with CUDA
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia -y

3. Install the required libraries:
pip install -r requirements.txt

4. Download the DeepLabCut weights at:
https://drive.google.com/drive/folders/1J8SNtwVYJroW1cTlSppY7jwjQ1Npf9fX?usp=sharing

5. Drag the weight files into
deeplabcut/dlc-models-pytorch/iteration-0/rtmposexAug25-trainset95shuffle1/train

6. Run the app in command prompt:
python main.py
