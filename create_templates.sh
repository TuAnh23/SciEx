#!/bin/bash
set -eu  # Crash if variable used without being set

rm -rf human_feedback_template
# Loop through each JSON exam file
for file in $(find exams_json/ -type f -name '*.json'); do
  python create_info_template.py --json_path ${file}
  python create_grading_template.py --json_path ${file}
done

