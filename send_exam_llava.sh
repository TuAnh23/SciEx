#!/bin/bash
set -eu  # Crash if variable used without being set

# Setting environment
source /home/tdinh/.bashrc
conda activate llminference
#conda activate /home/sparta/anaconda3/envs/llava
which python

export HF_HOME="/export/data1/tdinh/huggingface"
#export HF_HOME=/project/OML/tdinh/.cache/huggingface
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:512"

LLM_PATH="llava-hf/llava-1.5-7b-hf"
#LLM_PATH="liuhaotian/llava-v1.6-mistral-7b"
LLM_NAME="llava"

# Loop through each JSON file in the current directory and its subdirectories
for file in $(find exams_json/ -type f -name '*.json'); do
  echo "Processing exam at $file"
  echo "Format checking ... "
  python -u validate_exam_json.py \
    --json_path ${file}

  echo "Sending request to LLaVA ..."
  python -u send_exam_llava.py \
    --llm-path ${LLM_PATH} \
    --llm-name ${LLM_NAME} \
    --exam-json-path $file

  echo "---------------------------------------------------------"
done
