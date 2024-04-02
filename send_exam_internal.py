import text_generation
import json
import os
from utils import prompt_prefix, load_json, info_from_exam_path, write_text_file
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-url", default="http://i13hpc65:8054")
    parser.add_argument("--llm-name", default='mistral')
    parser.add_argument("--exam-json-path")
    args = parser.parse_args()

    exam_name, lang = info_from_exam_path(args.exam_json_path)
    prompt = prompt_prefix(lang=lang)
    exam = load_json(args.exam_json_path)

    out_dir = f"llm_out/{exam_name}"
    os.makedirs(out_dir, exist_ok=True)
    out_path = f"{out_dir}/{exam_name}_{lang}_{args.llm_name}.txt"

    if os.path.isfile(out_path):
        print("LLM output already available. Skip")
        exit()

    client = text_generation.Client(args.server_url, timeout=5000)
    print("Test request to see if server works: .........................")
    print(client.generate("Are you awake?", max_new_tokens=17).generated_text)
    print("Done testing")

    exam_out = ""
    for question in exam['Questions']:
        question_id = question.pop("Index")
        question_str = json.dumps(question)
        out = client.generate(f"{prompt} \n{question_str}", max_new_tokens=952).generated_text
        print(f"{prompt} \n{question_str}")
        print("question_out", out)

        exam_out += f"Answer to Question {question_id}\n"
        exam_out += f"{out}\n"
        exam_out += "\n\n\n\n\n****************************************************************************************\n"
        exam_out += "****************************************************************************************\n\n\n\n\n"

    write_text_file(exam_out, out_path)


if __name__ == "__main__":
    main()
