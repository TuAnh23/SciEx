import argparse
import os
from PIL import Image
from json import JSONDecodeError
from transformers import AutoProcessor, LlavaForConditionalGeneration
import json
from utils import prompt_prefix, info_from_exam_path, load_json, collect_figures
import logging
import fitz  # PyMuPDF, imported as fitz for backward compatibility reasons


def llava(model, processor, prompt, image_paths=[]):
    prompt = f"USER: <image>\n{prompt}ASSISTANT:"
    if len(image_paths) == 0:
        inputs = processor(text=prompt, return_tensors="pt")
    else:
        image = combine_images(image_paths)
        inputs = processor(text=prompt, images=image, return_tensors="pt")

    # Generate
    generate_ids = model.generate(**inputs, max_length=2048)
    text_from_lava = (
        processor.batch_decode(generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
    )
    # "\nUSER: What's the content of the image?\nASSISTANT: The image features a stop sign on a street corner"
    req_text = str(text_from_lava).split('ASSISTANT:')[-1]
    return req_text


def write_file(lava_text_list, output_path):
    with open(output_path, 'w') as f:
        json.dump(lava_text_list, f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm-path", default="llava-hf/llava-1.5-7b-hf")
    parser.add_argument("--llm-name", default='llava')
    parser.add_argument("--exam-json-path")
    args = parser.parse_args()

    exam_name, lang = info_from_exam_path(args.exam_json_path)
    out_dir = f"llm_out/{exam_name}"
    out_path = f"{out_dir}/{exam_name}_{lang}_{args.llm_name}.json"

    if os.path.isfile(out_path):
        print("LLM output already available. Skip")
        exit()

    os.makedirs(out_dir, exist_ok=True)

    logging.info("Loading model...")
    model = LlavaForConditionalGeneration.from_pretrained(args.llm_path)
    logging.info("Loading model completed.")

    logging.info("Loading processor...")
    processor = AutoProcessor.from_pretrained(args.llm_path)
    logging.info("Loading processor completed.")

    exam = load_json(args.exam_json_path)

    prompt = prompt_prefix(lang=lang, scope='per_question')

    exam_out = []
    count_invalid_json = 0
    for question in exam['Questions']:
        image_paths = collect_figures(question)
        image_paths = [f"exams_json/{exam_name}/{x}" for x in image_paths]

        question_str = json.dumps(question)
        prompt_per_question = f"{prompt} \n{question_str}"

        logging.info("Parsing question ...")
        print(f"{prompt} \n{question_str}")
        out = llava(model=model, processor=processor, prompt=prompt_per_question, image_paths=image_paths)
        logging.info("Answer received.")
        print("question_out", out)
        try:
            out_json = json.loads(out)
        except JSONDecodeError:
            out_json = out
            count_invalid_json = count_invalid_json + 1
        exam_out.append(out_json)

    exam_out = {"Answers": exam_out}

    with open(out_path, 'w') as f:
        json.dump(exam_out, f, indent=4)

    print(f"count_invalid_json {count_invalid_json}")


def pdf2pil(pdf_path):
    images = []
    doc = fitz.open(pdf_path)  # open document
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=300)  # render page to an image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images


def combine_images(image_paths):
    # Open all images and store them in a list
    images = []
    for path in image_paths:
        if path.endswith('.pdf'):
            images.extend(
                pdf2pil(path)
            )
        else:
            images.append(Image.open(path))

    # Find the maximum width and height among all images
    max_width = max(image.width for image in images)
    max_height = max(image.height for image in images)

    # Create a new blank image with the maximum width and height
    combined_image = Image.new('RGB', (max_width, max_height * len(images)))

    # Paste each image onto the blank image, padding if necessary
    y_offset = 0
    for image in images:
        x_offset = (max_width - image.width) // 2  # calculate horizontal padding
        combined_image.paste(image, (x_offset, y_offset))
        y_offset += max_height

    return combined_image


if __name__ == "__main__":
    main()
