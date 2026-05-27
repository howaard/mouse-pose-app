import os
import csv
import re
import json
import torch
import torch.nn as nn
import numpy as np
import pandas as pd 
import networkx as nx
from torch.nn import TransformerEncoderLayer, TransformerEncoder

# --- 1. Preprocessing Logic ---
def preprocess_csv(input_path, output_path, progress_callback):
    progress_callback(" > Formatting 2D CSV for PyTorch consumption...")
    with open(input_path, mode='r', newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        data = list(reader)

    if len(data) > 1: del data[1]
        
    for row_idx, row in enumerate(data):
        for col_idx in range(len(row)):
            cell = row[col_idx]
            if 1 <= col_idx <= 63: cell = re.sub(r'^\d+_', '', cell)
            if '.png' in cell.lower():
                filename = re.split(r'[\\/]', cell)[-1]
                filename = re.sub(r'\.png$', '', filename, flags=re.IGNORECASE)
                cell = filename.capitalize()
            row[col_idx] = cell

    with open(output_path, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerows(data)

# --- 2. Model Architecture ---
def precompute_spatial_embedding(skeleton_bones, num_joints, num_heads, max_dist=10):
    G = nx.Graph()
    G.add_edges_from(skeleton_bones)
    path_lengths = dict(nx.all_pairs_shortest_path_length(G, cutoff=max_dist))
    distance_matrix = torch.full((num_joints, num_joints), fill_value=max_dist, dtype=torch.long)
    for i in range(num_joints):
        for j in range(num_joints):
            if i == j: distance_matrix[i, j] = 0
            elif j in path_lengths.get(i, {}): distance_matrix[i, j] = path_lengths[i][j]
    return nn.Embedding(num_embeddings=max_dist + 1, embedding_dim=num_heads), distance_matrix

class FusedGraphAttentionBlock(nn.Module):
    def __init__(self, model_dim, num_heads, mlp_dim, dropout_rate=0.1):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = model_dim // num_heads
        self.norm1 = nn.LayerNorm(model_dim)
        self.to_qkv = nn.Linear(model_dim, model_dim * 3)
        self.to_out = nn.Linear(model_dim, model_dim)
        self.norm2 = nn.LayerNorm(model_dim)
        self.mlp = nn.Sequential(nn.Linear(model_dim, mlp_dim), nn.GELU(), nn.Linear(mlp_dim, model_dim))
        self.attn_dropout = nn.Dropout(dropout_rate)
        self.mlp_dropout = nn.Dropout(dropout_rate)

    def forward(self, x, graph_bias, confidence):
        res1 = x
        x_norm = self.norm1(x)
        qkv = self.to_qkv(x_norm).chunk(3, dim=-1)
        q, k, v = map(lambda t: t.reshape(t.shape[0], t.shape[1], self.num_heads, self.head_dim).permute(0, 2, 1, 3), qkv)
        
        v = v * confidence.unsqueeze(1)
        scores = torch.matmul(q, k.transpose(-1, -2)) / (self.head_dim ** 0.5)
        biased_scores = scores + graph_bias
        attn = torch.softmax(biased_scores, dim=-1)
        out = torch.matmul(attn, v)
        out = out.permute(0, 2, 1, 3).reshape(x.shape[0], x.shape[1], -1)
        x = res1 + self.attn_dropout(self.to_out(out))

        res2 = x
        x_norm = self.norm2(x)
        mlp_out = self.mlp(x_norm)
        x = res2 + self.mlp_dropout(mlp_out)
        return x

class SpatioTemporalPoseTransformer(nn.Module):
    def __init__(self, num_joints, model_dim, num_spatial_layers, num_temporal_layers, num_heads, skeleton_bones, dropout_rate=0.1):
        super().__init__()
        self.input_embedding = nn.Linear(3, model_dim) 
        self.positional_embedding = nn.Parameter(torch.randn(1, num_joints, model_dim))
        self.spatial_embedding_layer, distance_matrix = precompute_spatial_embedding(skeleton_bones, num_joints, num_heads)
        self.register_buffer('distance_matrix', distance_matrix)
        self.layers = nn.ModuleList([FusedGraphAttentionBlock(model_dim, num_heads, model_dim * 4, dropout_rate) for _ in range(num_spatial_layers)])
        
        temporal_layer = TransformerEncoderLayer(d_model=model_dim, nhead=num_heads, dim_feedforward=model_dim * 4, dropout=dropout_rate, batch_first=True)
        self.temporal_encoder = TransformerEncoder(temporal_layer, num_layers=num_temporal_layers)
        self.output_head = nn.Linear(model_dim, 3)

    def get_graph_bias(self):
        graph_bias_lookup = self.spatial_embedding_layer(self.distance_matrix)
        return graph_bias_lookup.permute(2, 0, 1)

    def forward(self, x_coords_seq):
        B, T, N, _ = x_coords_seq.shape
        coords_flat = x_coords_seq.view(B * T, N, 3)
        x = self.input_embedding(coords_flat) + self.positional_embedding
        confidence = coords_flat[:, :, 2:3]
        graph_bias = self.get_graph_bias()
        
        for layer in self.layers: x = layer(x, graph_bias, confidence)
        
        spatial_features = x.view(B, T, N, -1)
        joint_trajectories = spatial_features.permute(0, 2, 1, 3).reshape(B * N, T, -1)
        temporal_features = self.temporal_encoder(joint_trajectories)
        final_joint_features = temporal_features[:, -1, :]
        
        # Ensure it returns a [B, N, 3] shaped tensor, not a flattened array
        out_flat = self.output_head(final_joint_features)
        return out_flat.view(B, N, 3)

# --- 3. Main Execution Controller ---
def run_3d_pipeline(input_2d_csv_path, output_folder, models_folder, progress_callback, is_running_func):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    progress_callback(f" > Initialized PyTorch using device: {device.upper()}")
    
    reformatted_csv_path = input_2d_csv_path.replace('.csv', '_reformatted.tmp.csv')
    preprocess_csv(input_2d_csv_path, reformatted_csv_path, progress_callback)
    
    model_path = os.path.join(models_folder, 'fgf_temporal_baseline_v2.pth')
    rig_data_path = os.path.join(models_folder, 'rig_data.json')
    norm_stats_path = os.path.join(models_folder, 'normalization_stats_temporal_baseline_v2.json')
    
    with open(rig_data_path, 'r') as f: rig_data = json.load(f)
    with open(norm_stats_path, 'r') as f: norm_stats = json.load(f)
        
    num_joints = len(rig_data['processing_order'])
    skeleton_bones_idx = [[rig_data['processing_order'].index(p), rig_data['processing_order'].index(c)] for p, c in rig_data['kinematic_chain']]

    model = SpatioTemporalPoseTransformer(
        num_joints=num_joints, model_dim=256, num_spatial_layers=4, 
        num_temporal_layers=2, num_heads=4, skeleton_bones=skeleton_bones_idx, dropout_rate=0.0
    ).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    
    sequence_length = 9
    try:
        df_raw = pd.read_csv(reformatted_csv_path, header=[0, 1, 2], index_col=0)
        num_frames = len(df_raw)
        progress_callback(f" > Extracting sequences across {num_frames} frames...")
    except Exception as e:
        progress_callback(f"❌ Error loading reformatted CSV file: {e}")
        return

    all_predicted_poses_relative = []
    start_index = sequence_length - 1
    
    mean = torch.tensor(norm_stats['mean'], dtype=torch.float32, device=device)
    std = torch.tensor(norm_stats['std'], dtype=torch.float32, device=device)
    std[std < 1e-8] = 1e-8
    core_indices = norm_stats['core_body_indices']
    root_idx = norm_stats['root_joint_idx']
    
    with torch.no_grad():
        for end_frame_idx in range(start_index, num_frames):
            if not is_running_func(): return
            
            start_frame_index = end_frame_idx - sequence_length + 1
            sequence_series = df_raw.iloc[start_frame_index : end_frame_idx + 1]

            target_joint_order = rig_data['processing_order']
            temp_df = sequence_series.copy()
            temp_df.columns = temp_df.columns.get_level_values('bodyparts')
            reordered_df = temp_df[target_joint_order]
            pose_2d_raw_seq_tensor = torch.tensor(reordered_df.values, dtype=torch.float32).reshape(sequence_length, num_joints, 3)

            coords_xy_raw_seq = pose_2d_raw_seq_tensor[:, :, :2].to(device)
            confidence_raw_seq = pose_2d_raw_seq_tensor[:, :, 2:3].to(device)
            
            core_coords = coords_xy_raw_seq[:, core_indices, :]
            min_coords, _ = torch.min(core_coords.reshape(-1, 2), dim=0)
            max_coords, _ = torch.max(core_coords.reshape(-1, 2), dim=0)
            scale = torch.norm(max_coords - min_coords) + 1e-8
            
            root_coords = coords_xy_raw_seq[:, root_idx:root_idx+1, :]
            centered = coords_xy_raw_seq - root_coords
            scaled = centered / scale
            normalized_coords = (scaled - mean) / std
            
            pose_2d_final_seq = torch.cat([normalized_coords, confidence_raw_seq], dim=2)
            poses_2d_seq_batch = pose_2d_final_seq.unsqueeze(0)

            # Extract relative normalized output! Shape: [1, N, 3] -> Append Batch 0 -> [N, 3]
            pred_coords_relative = model(poses_2d_seq_batch)
            all_predicted_poses_relative.append(pred_coords_relative[0].cpu().numpy())

    if all_predicted_poses_relative:
        progress_callback(" > Packing 3D DataFrames (With Frame Padding to match Video Length)...")
        final_coords_array = np.stack(all_predicted_poses_relative)
        
        # PADDING: Duplicate the first prediction to fill frames 0-7 so the lengths perfectly match
        pad_length = sequence_length - 1
        first_frame_duplicated = np.repeat(final_coords_array[0:1], pad_length, axis=0)
        padded_coords_array = np.concatenate([first_frame_duplicated, final_coords_array], axis=0)
        
        base_name = os.path.basename(input_2d_csv_path).replace('2D_', '').replace('.csv', '')
        npy_output_path = os.path.join(output_folder, f"3D_{base_name}.npy")
        csv_output_path = os.path.join(output_folder, f"3D_{base_name}.csv")
        
        np.save(npy_output_path, padded_coords_array)
        
        original_scorer = "Model_3D"
        new_columns = []
        for bp in target_joint_order:
            new_columns.extend([(original_scorer, bp, 'x'), (original_scorer, bp, 'y'), (original_scorer, bp, 'z')])
            
        multi_index = pd.MultiIndex.from_tuples(new_columns, names=['scorer', 'bodyparts', 'coords'])
        flattened_coords_array = padded_coords_array.reshape(padded_coords_array.shape[0], -1)
        
        df_out = pd.DataFrame(flattened_coords_array, index=df_raw.index, columns=multi_index)
        df_out.to_csv(csv_output_path)
        
        progress_callback(f"✅ 3D Inference Complete!")
    
    if os.path.exists(reformatted_csv_path): os.remove(reformatted_csv_path)