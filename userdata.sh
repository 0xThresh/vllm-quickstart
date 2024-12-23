#!/bin/bash

# Install Conda
mkdir -p /usr/lib/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-py310_24.11.1-0-Linux-x86_64.sh -O /usr/lib/miniconda3/miniconda.sh
bash /usr/lib/miniconda3/miniconda.sh -b -u -p /usr/lib/miniconda3/
rm /usr/lib/miniconda3/miniconda.sh

# Set up vLLM
conda create -n vllm python=3.10 -y
conda activate vllm
pip install vllm
vllm serve Qwen/Qwen2.5-1.5B-Instruct

# TODO: Set up DataDog agent 