1. Create a new conda environment: 
conda create -n mouse python=3.10.16
conda activate mouse

2. Install PyTorch with CUDA
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia -y

3. Install the required libraries:
pip install -r requirements.txt

4. Run the app in command prompt:
python main.py