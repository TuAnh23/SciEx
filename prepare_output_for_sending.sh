#!/bin/bash

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