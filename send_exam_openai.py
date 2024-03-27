from openai import OpenAI
import json
import os
from utils import prompt_prefix, load_json, write_text_file, info_from_exam_path, collect_figures, encode_image, process_images
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-url", default="openai")
    parser.add_argument("--llm-name-full", default="gpt-3.5-turbo-0125")
    parser.add_argument("--llm-name", default='gpt35')
    parser.add_argument("--exam-json-path")
    args = parser.parse_args()

    if args.server_url != "openai":
        client = OpenAI(base_url=args.server_url, timeout=1800)
    else:
        client = OpenAI(timeout=1800)

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
        if "vision" in args.llm_name_full:
            images = process_images(exam_name, question)
            images_messages = [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{encode_image(pil_image=image)}"}
                }
                for image in images
            ]
            text_message = {
                "type": "text",
                "text": json.dumps(question)
            }
            message = [text_message] + images_messages

            response = client.chat.completions.create(
                model=args.llm_name_full,
                seed=0,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": message}
                ]
            )
        else:
            response = client.chat.completions.create(
                model=args.llm_name_full,
                seed=0,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": json.dumps(question)}
                ]
            )
        out = response.choices[0].message.content
        exam_out += f"Answer to Question {question_id}\n"
        exam_out += f"{out}\n"
        exam_out += \
            "\n\n\n\n\n****************************************************************************************\n"
        exam_out += "****************************************************************************************\n\n\n\n\n"

    write_text_file(exam_out, out_path)


if __name__ == "__main__":
    main()
