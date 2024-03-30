import argparse
import os
from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration
import transformers
import json
from utils import prompt_prefix, info_from_exam_path, load_json, process_images, combine_images, write_text_file
import logging
from PIL import Image


def llava(model, processor, prompt, image=None):
    prompt = f"USER: <image>\n{prompt}ASSISTANT:"
    if image is None:
        # Only needed for llava 1.5
        # blank_image = create_blank_image()
        # inputs = processor(text=prompt, images=blank_image, return_tensors="pt")

        inputs = processor(text=prompt, return_tensors="pt")
    else:
        inputs = processor(text=prompt, images=image, return_tensors="pt")

    inputs = inputs.to('cuda')

    # Generate
    generate_ids = model.generate(**inputs, max_length=2048)
    text_from_lava = (
        processor.batch_decode(generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
    )
    # "\nUSER: What's the content of the image?\nASSISTANT: The image features a stop sign on a street corner"
    req_text = str(text_from_lava).split('ASSISTANT:')[-1]
    return req_text


def create_blank_image():
    # Define the size of the image (width, height)
    width = 500
    height = 300
    # Define the color for the blank image (in RGB format)
    background_color = (0, 0, 0)  # Black color
    # Create a new blank image
    blank_image = Image.new("RGB", (width, height), background_color)
    return blank_image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm-path", default="llava-hf/llava-1.5-7b-hf")
    parser.add_argument("--llm-name", default='llava')
    parser.add_argument("--exam-json-path")
    args = parser.parse_args()

    print(f"Transformers version: {transformers.__version__}")

    exam_name, lang = info_from_exam_path(args.exam_json_path)
    out_dir = f"llm_out/{exam_name}"
    out_path = f"{out_dir}/{exam_name}_{lang}_{args.llm_name}.txt"

    if os.path.isfile(out_path):
        print("LLM output already available. Skip")
        exit()

    os.makedirs(out_dir, exist_ok=True)

    logging.info("Loading model...")
    model = LlavaNextForConditionalGeneration.from_pretrained(args.llm_path)
    model.to('cuda')
    logging.info("Loading model completed.")

    logging.info("Loading processor...")
    processor = LlavaNextProcessor.from_pretrained(args.llm_path)
    logging.info("Loading processor completed.")

    exam = load_json(args.exam_json_path)

    prompt = prompt_prefix(lang=lang, stack_figures=True)

    exam_out = ''
    for question in exam['Questions']:
        images = process_images(exam_name, question)
        if len(images) > 0:
            image = combine_images(images)
        else:
            image = None

        question_id = question.pop("Index")
        question_str = json.dumps(question)
        prompt_per_question = f"{prompt} \n{question_str}"

        logging.info("Parsing question ...")
        print(f"{prompt} \n{question_str}")
        out = llava(model=model, processor=processor, prompt=prompt_per_question, image=image)
        logging.info("Answer received.")
        print("question_out", out)

        exam_out += f"Answer to Question {question_id}\n"
        exam_out += f"{out}\n"
        exam_out += \
            "\n\n\n\n\n****************************************************************************************\n"
        exam_out += "****************************************************************************************\n\n\n\n\n"

    write_text_file(exam_out, out_path)


if __name__ == "__main__":
    main()
