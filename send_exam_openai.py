from openai import OpenAI
import json
import os
from utils import prompt_prefix, load_json, dump_json, info_from_exam_path, collect_figures
import argparse
import base64
from json import JSONDecodeError
import requests


# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-url", default="openai")
    parser.add_argument("--llm-name-full", default="gpt-3.5-turbo-0125")
    parser.add_argument("--llm-name", default='gpt35')
    parser.add_argument("--exam-json-path")
    args = parser.parse_args()

    if args.server_url != "openai":
        client = OpenAI(base_url=args.server_url)
    else:
        client = OpenAI()

    exam_name, lang = info_from_exam_path(args.exam_json_path)
    prompt = prompt_prefix(lang, scope='per_question')
    exam = load_json(f"exams_json/{exam_name}/{exam_name}_{lang}.json")

    exam_out = []
    count_invalid_json = 0
    for question in exam['Questions']:
        if "vision" in args.llm_name_full:
            image_paths = collect_figures(question)
            image_full_paths = [f"exams_json/{exam_name}/{x}" for x in image_paths]
            images_messages = [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{encode_image(image_path)}"}
                }
                for image_path in image_full_paths
            ]
            text_message = {
                "type": "text",
                "text": json.dumps(question)
            }
            message = [text_message] + images_messages

            response = client.chat.completions.create(
                model=args.llm_name_full,
                response_format={"type": "json_object"},
                seed=0,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": message}
                ]
            )
        else:
            response = client.chat.completions.create(
                model=args.llm_name_full,
                response_format={"type": "json_object"},
                seed=0,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": json.dumps(question)}
                ]
            )
        out = response.choices[0].message.content
        try:
            out_json = json.loads(out)
        except JSONDecodeError:
            out_json = out
            count_invalid_json = count_invalid_json + 1
        exam_out.append(out_json)

    exam_out = {"Answers": exam_out}

    out_dir = f"llm_out/{exam_name}"
    os.makedirs(out_dir, exist_ok=True)

    dump_json(exam_out, f"{out_dir}/{exam_name}_{lang}_{args.llm_name}.json")


if __name__ == "__main__":
    main()
