"""This module is fol calculation of datasets' statistics for FID evaluation"""

from utils.fid_score import calculate_activation_statistics
from argparse import ArgumentParser
import numpy as np
from utils.inception_score import InceptionV3
import torch
import os

def main(args):
    save_path = "datasets_stats"
    block_idx = InceptionV3.BLOCK_INDEX_BY_DIM[2048]
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    model = InceptionV3([block_idx]).to(device)
    mu, sigma = calculate_activation_statistics(args.path, model)
    
    os.mkdir(save_path, exists_ok=True)
    np.save(os.path.join(save_path, f"{args.dataset_name}.npz"), mu=mu, sigma=sigma)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-nm", "--dataset_name", default=None, type=str, help="name of the current dataset")
    parser.add_argument("-p", "--path", default=None, type=str, help="path to dataset dir")
    # parser.add_argument("-sp", "--save_path", default=None, type=str, help="path for saving statistics")
    args = parser.parse_args()
    main(args)