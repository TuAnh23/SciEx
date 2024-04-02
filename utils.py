import json
import os
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF, imported as fitz for backward compatibility reasons
import base64
import io


def map_llm_to_index(llm_name):
    llm_list = ['llava', 'mistral', 'mixtral', 'qwen', 'claude', 'gpt35', 'gpt4v']
    if llm_name not in llm_list:
        raise RuntimeError(f"LLM {llm_name} not in list")
    d = {llm: f"llm{i}" for i, llm in enumerate (llm_list)}
    return d[llm_name]


def prompt_prefix(lang, stack_figures=False):
    """
    :param lang: 'en' or 'de'
    :return: prompt prefix as a string
    """
    if stack_figures:
        if lang == 'en':
            extra_message = "Note that the single input figure could contain multiple figures stacked vertically. "
        elif lang == 'de':
            extra_message = "Beachten Sie, dass die einzelne Eingabe Figur mehrere vertikal gestapelte Figuren enthalten kann. "
        else:
            raise RuntimeError(f"No prompt for lang {lang}")
    else:
        extra_message = ""
    if lang == 'en':
        prompt = "You are a university student. Please answer the following JSON-formatted exam question. " \
                 "The subquestions (if any) are indexed. " \
                 "The provided figures (if any) each contains its path at the bottom, " \
                 f"which matches the path provided in the JSON. {extra_message}" \
                 "Please give the answers to the question and subquestions that were asked, " \
                 "and index them accordingly in your output. " \
                 "You do not have to provide your output in the JSON format. " \
                 "If you are asked to draw on the figure, then describe with words how you would draw it. " \
                 "Please provide all answers in English. " \
                 "Here is the question: \n"
    elif lang == 'de':
        prompt = "Sie sind Student. Bitte beantworten Sie die folgende JSON-formatierte Prüfungsfrage. " \
                 "Die Unterfragen (falls vorhanden) sind indiziert. " \
                 "Die bereitgestellten Abbildungen (falls vorhanden) enthalten jeweils unten ihren Pfad, " \
                 f"der mit dem im JSON bereitgestellten Pfad übereinstimmt. {extra_message}" \
                 "Bitte geben Sie die Antworten auf die gestellten Fragen " \
                 "und Unterfragen an und indizieren Sie diese in Ihrer Ausgabe entsprechend. " \
                 "Sie müssen Ihre Ausgabe nicht im JSON-Format bereitstellen. " \
                 "Wenn Sie aufgefordert werden, auf der Figur zu zeichnen, beschreiben Sie mit Worten, wie Sie sie zeichnen würden. " \
                 "Bitte geben Sie alle Antworten auf Deutsch an. Hier ist die Frage: \n"
    else:
        raise RuntimeError(f"No prompt for lang {lang}")

    return prompt


def load_json(file_path):
    with open(file_path, 'r') as f:
        obj = json.load(f)
    return obj


def dump_json(obj, file_path):
    with open(file_path, 'w') as f:
        json.dump(obj, f, indent=4)


def info_from_exam_path(exam_json_path):
    exam_name = exam_json_path.split('/')[-2]
    lang = exam_json_path.split('/')[-1].replace('.json', '').split('_')[-1]
    assert os.path.isfile(f"exams_json/{exam_name}/{exam_name}_{lang}.json")
    assert lang in ['en', 'de']
    return exam_name, lang


def collect_figures(question_dict):
    figure_list = []
    if 'Figures' in question_dict:
        figure_list.extend(question_dict['Figures'])
    if 'Subquestions' in question_dict:
        for subquestion_dict in question_dict['Subquestions']:
            if 'Figures' in subquestion_dict:
                figure_list.extend(subquestion_dict['Figures'])
    return figure_list


def add_title(img, title):
    # Create a black bar with the same width as the image and some height for the title
    black_bar_height = 50
    black_bar = Image.new('RGB', (img.width, black_bar_height), color='black')

    # Combine the image with the black bar
    new_img = Image.new('RGB', (img.width, img.height + black_bar_height))
    new_img.paste(img, (0, 0))
    new_img.paste(black_bar, (0, img.height))

    # Draw the title text on the black bar
    draw = ImageDraw.Draw(new_img)
    fontsize = 20
    font = ImageFont.truetype("artifacts/Arial.ttf", size=fontsize)
    text_width = draw.textlength(title, font=font)
    text_height = fontsize
    text_position = ((img.width - text_width) // 2, img.height + (black_bar_height - text_height) // 2)
    draw.text(text_position, title, fill='white', font=font)

    return new_img


def pdf2pil(pdf_path):
    images = []
    doc = fitz.open(pdf_path)  # open document
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=300)  # render page to an image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images


def combine_images(images):
    # Find the maximum width and height among all images
    max_width = max(int(image.width*1.1) for image in images)
    height_gap = max(int(image.height*0.05) for image in images)
    total_height = sum(image.height for image in images) + height_gap * (len(images) + 1)

    # Create a new blank image with the maximum width and height
    combined_image = Image.new('RGB', (max_width, total_height))

    # Paste each image onto the blank image, padding if necessary
    y_offset = height_gap
    for image in images:
        x_offset = (max_width - image.width) // 2  # calculate horizontal padding
        combined_image.paste(image, (x_offset, y_offset))
        y_offset = y_offset + image.height + height_gap

    return combined_image


def load_images(image_paths):
    """
    :param image_paths: path to the images. can be pdf file containing multiple pages
    :return: images: list of single images loaded by PIL. images_paths_flatten: path of each single image
    """
    images = []
    images_paths_flatten = []
    for path in image_paths:
        if path.endswith('.pdf'):
            images_tmp = pdf2pil(path)
            images.extend(images_tmp)
            images_paths_flatten.extend([path] * len(images_tmp))
        else:
            images.append(Image.open(path))
            images_paths_flatten.append(path)
    return images, images_paths_flatten


def write_text_file(string, file_path):
    with open(file_path, 'w') as file:
        file.write(string)


def encode_image(image_path=None, pil_image=None):
    if image_path is not None:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    if pil_image is not None:
        # Create an in-memory binary stream (bytes-like object)
        image_stream = io.BytesIO()
        # Save the PIL image to the in-memory stream in PNG format
        pil_image.save(image_stream, format='PNG')
        # Seek to the beginning of the stream
        image_stream.seek(0)
        # Encode the image data as base64 and decode it to convert from bytes to string
        encoded_image = base64.b64encode(image_stream.read()).decode('utf-8')
        return encoded_image


def process_images(exam_name, question):
    image_paths = collect_figures(question)
    image_full_paths = [f"exams_json/{exam_name}/{x}" for x in image_paths]
    images, image_full_paths_flatten = load_images(image_full_paths)
    image_paths_flatten = [path.replace(f"exams_json/{exam_name}/", "") for path in image_full_paths_flatten]
    image_titles = [f"Figure: {x}" for x in image_paths_flatten]
    images = [add_title(img, title) for img, title in zip(images, image_titles)]
    return images