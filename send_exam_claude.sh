#!/bin/bash
set -eu  # Crash if variable used without being set

# Setting environment
source /home/tdinh/.bashrc
conda activate llminference
which python

LLM_NAME="claude"
LLM_NAME_FULL="claude-3-opus-20240229"

# Loop through each JSON file in the current directory and its subdirectories
for file in $(find exams_json/ -type f -name '*.json'); do
  echo "Processing exam at $file"
  echo "Format checking ... "
  python -u validate_exam_json.py \
    --json_path ${file}

  echo "Sending request to claude ..."
  python -u send_exam_claude.py \
    --llm-name-full ${LLM_NAME_FULL} \
    --llm-name ${LLM_NAME} \
    --exam-json-path ${file}

  echo "---------------------------------------------------------"
done
