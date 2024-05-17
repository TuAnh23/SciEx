#!/bin/bash
set -eu  # Crash if variable used without being set

# Setting environment
source /home/tdinh/.bashrc
conda activate llminference
#. .venv/bin/activate
#conda activate py39
#. .llava/bin/activate
which python


SERVER_TYPE=$1
LLM_NAME=$2
LLM_NAME_FULL=$3
SERVER_URL=$4

if [ -z ${SERVER_TYPE} ]; then
  SERVER_TYPE="openai"
fi
if [ -z ${LLM_NAME} ]; then
  LLM_NAME="mixtral"
fi
if [ -z ${LLM_NAME_FULL} ]; then
  LLM_NAME_FULL=mistralai/Mixtral-8x7B-Instruct-v0.1
fi
if [ -z ${SERVER_URL} ]; then
  SERVER_URL="http://i13hpc65:8080"  # Local mixtral lamma.cpp
fi

# Loop through each JSON file in the current directory and its subdirectories
for file in $(find exams_json/ -type f -name '*.json'); do
  echo "Processing exam at $file"
  echo "Format checking ... "
  python -u validate_exam_json.py \
    --json_path ${file}

  echo "Sending request ..."
  python -u llm_solve_exam.py \
    --server-type ${SERVER_TYPE} \
    --server-url ${SERVER_URL} \
    --llm-name-full ${LLM_NAME_FULL} \
    --llm-name ${LLM_NAME} \
    --exam-json-path ${file}

  echo "---------------------------------------------------------"
done
