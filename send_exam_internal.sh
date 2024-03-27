#!/bin/bash
set -eu  # Crash if variable used without being set

# Setting environment
source /home/tdinh/.bashrc
conda activate llminference
which python

LLM_NAME=mixtral
SERVER_URL="http://i13hpc65:8054"

# Loop through each JSON file in the current directory and its subdirectories
for file in $(find exams_json/ -type f -name '*.json'); do
  echo "Processing exam at $file"
  echo "Format checking ... "
  python -u validate_exam_json.py \
    --json_path ${file}

  echo "Sending request to locally hosted LLM ..."
  python -u send_exam_internal.py \
    --server-url ${SERVER_URL} \
    --llm-name ${LLM_NAME} \
    --exam-json-path ${file}

  echo "---------------------------------------------------------"
done
