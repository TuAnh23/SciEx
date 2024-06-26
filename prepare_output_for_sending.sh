#!/bin/bash

rm -rf human_feedback_template
# Loop through each JSON exam file
for file in $(find exams_json/ -type f -name '*.json'); do
  python create_info_template.py --json_path ${file}
  python create_grading_template.py --json_path ${file}
  python prepare_llm_output.py --json_path ${file}
done

parent_directory="llm_out_filtered"

# Loop through each subdirectory in the parent directory
for subdirectory in "$parent_directory"/*/; do
    # Extract the name of the subdirectory
    subdirectory_name=$(basename "$subdirectory")

    # Create the output file name
    output_file="$parent_directory/${subdirectory_name}_llm_out.tar.gz"

    # Compress the subdirectory using tar
    tar -czf "$output_file" -C "$parent_directory" "$subdirectory_name"
done



parent_directory="human_feedback_template"

# Loop through each subdirectory in the parent directory
for subdirectory in "$parent_directory"/*/; do
    # Extract the name of the subdirectory
    subdirectory_name=$(basename "$subdirectory")

    # Create the output file name
    output_file="$parent_directory/${subdirectory_name}_templates.tar.gz"

    # Compress the subdirectory using tar
    tar -czf "$output_file" -C "$parent_directory" "$subdirectory_name"
done