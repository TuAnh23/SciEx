import argparse
import os
import shutil

from utils import map_llm_to_index


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json_path", type=str)

    args = parser.parse_args()

    exam_name = args.json_path.split('/')[-2]
    exam_name_lang = args.json_path.split('/')[-1].replace('.json', '')
    out_dir = f"llm_out_filtered/{exam_name}"
    os.makedirs(out_dir, exist_ok=True)

    for llm in ['llava', 'mistral', 'mixtral', 'qwen', 'claude', 'gpt35', 'gpt4v']:
        original_output_file = f"llm_out/{exam_name}/{exam_name_lang}_{llm}.txt"
        filtered_output_file = f"llm_out_filtered/{exam_name}/{exam_name_lang}_{map_llm_to_index(llm)}.txt"

        if not os.path.isfile(original_output_file):
            raise RuntimeError(f"Missing LLM output file {original_output_file}")
        shutil.copyfile(original_output_file, filtered_output_file)


if __name__ == "__main__":
    main()
