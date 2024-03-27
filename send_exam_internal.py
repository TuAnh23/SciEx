import text_generation
import json
from json import JSONDecodeError
import os
from utils import prompt_prefix, load_json, dump_json, info_from_exam_path
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-url", default="http://i13hpc65:8054")
    parser.add_argument("--llm-name", default='mistral')
    parser.add_argument("--exam-json-path")
    args = parser.parse_args()

    exam_name, lang = info_from_exam_path(args.exam_json_path)
    prompt = prompt_prefix(lang=lang, scope='per_question')
    exam = load_json(args.exam_json_path)

    out_dir = f"llm_out/{exam_name}"
    os.makedirs(out_dir, exist_ok=True)
    out_path = f"{out_dir}/{exam_name}_{lang}_{args.llm_name}.json"

    if os.path.isfile(out_path):
        print("LLM output already available. Skip")
    else:
        client = text_generation.Client(args.server_url, timeout=5000)
        print("Test request to see if server works: .........................")
        print(client.generate("Are you awake?", max_new_tokens=17).generated_text)
        print("Done testing")

        exam_out = []
        count_invalid_json = 0
        for question in exam['Questions']:
            question_str = json.dumps(question)
            out = client.generate(f"{prompt} \n{question_str}", max_new_tokens=512).generated_text
            print(f"{prompt} \n{question_str}")
            print("question_out", out)
            try:
                out_json = json.loads(out)
            except JSONDecodeError:
                out_json = out
                count_invalid_json = count_invalid_json + 1
            exam_out.append(out_json)

        exam_out = {"Answers": exam_out}
        dump_json(exam_out, out_path)

        print(f"count_invalid_json {count_invalid_json}")


if __name__ == "__main__":
    main()
