import json
import os
from utils import prompt_prefix, load_json, write_text_file, info_from_exam_path, process_images
import argparse
from llm_clients import OpenAIClient, ClaudeClient, HFTextGenClient, HFLlava


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-type", choices=['openai', 'claude', 'hf_text_gen', 'hf_llava'])
    parser.add_argument("--server-url", default="openai")
    parser.add_argument("--llm-name-full", default="gpt-3.5-turbo-0125")
    parser.add_argument("--llm-name", default='gpt35')
    parser.add_argument("--exam-json-path")
    args = parser.parse_args()

    if args.server_type == 'openai':
        llm_client = OpenAIClient(model=args.llm_name_full, server_url=args.server_url, seed=0)
    elif args.server_type == 'claude':
        llm_client = ClaudeClient(model=args.llm_name_full)
    elif args.server_type == 'hf_text_gen':
        llm_client = HFTextGenClient(model=args.llm_name_full, server_url=args.server_url)
    elif args.server_type == 'hf_llava':
        llm_client = HFLlava(model=args.llm_name_full, device='cuda')
    else:
        raise RuntimeError(f"server_type {args.server_type} not implemented.")

    exam_name, lang = info_from_exam_path(args.exam_json_path)
    out_dir = f"llm_out/{exam_name}"
    out_path = f"{out_dir}/{exam_name}_{lang}_{args.llm_name}.txt"

    if os.path.isfile(out_path):
        print("LLM output already available. Skip")
        exit()

    os.makedirs(out_dir, exist_ok=True)

    prompt = prompt_prefix(lang)
    exam = load_json(f"exams_json/{exam_name}/{exam_name}_{lang}.json")

    exam_out = ''
    for question in exam['Questions']:
        question_id = question.pop("Index")
        print(question)

        out = llm_client.send_request(
            prompt,
            input_body=json.dumps(question),
            images=process_images(exam_name, question)
        )

        print(f'**** Answer: {out}')
        exam_out += f"Answer to Question {question_id}\n"
        exam_out += f"{out}\n"
        exam_out += \
            "\n\n\n\n\n****************************************************************************************\n"
        exam_out += "****************************************************************************************\n\n\n\n\n"

    write_text_file(exam_out, out_path)


if __name__ == "__main__":
    main()
