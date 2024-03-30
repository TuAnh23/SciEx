import anthropic
import json
import os
from utils import prompt_prefix, load_json, write_text_file, info_from_exam_path, encode_image, process_images
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm-name-full", default="claude-3-opus-20240229")
    parser.add_argument("--llm-name", default='claude')
    parser.add_argument("--exam-json-path")
    args = parser.parse_args()

    client = anthropic.Anthropic()

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

        images = process_images(exam_name, question)
        images_messages = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": encode_image(pil_image=image)
                }
            }
            for image in images
        ]
        text_message = {
            "type": "text",
            "text": json.dumps(question)
        }
        message = images_messages + [text_message]

        response = client.messages.create(
            model=args.llm_name_full,
            max_tokens=1000,
            temperature=0.0,
            system=prompt,
            messages=[
                {"role": "user", "content": message}
            ]
        )

        out = response.content[0].text
        exam_out += f"Answer to Question {question_id}\n"
        exam_out += f"{out}\n"
        exam_out += \
            "\n\n\n\n\n****************************************************************************************\n"
        exam_out += "****************************************************************************************\n\n\n\n\n"

    write_text_file(exam_out, out_path)


if __name__ == "__main__":
    main()
