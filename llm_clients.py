from openai import OpenAI
from abc import ABC, abstractmethod
from utils import encode_image, combine_images
import anthropic
import text_generation
import logging
from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration
from PIL import Image
import time


class LLMClient(ABC):
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def send_request(self, prompt, input_body, images, **kwargs):
        pass


class OpenAIClient(LLMClient):
    def __init__(self, model, server_url="openai", seed=0):
        super(OpenAIClient, self).__init__()
        self.server_url = server_url
        self.model = model
        self.seed = seed
        if self.server_url != "openai":
            self.client = OpenAI(base_url=self.server_url, timeout=900)
        else:
            self.client = OpenAI(timeout=900)

    def send_request(self, prompt, input_body, images, **kwargs):
        time.sleep(30)
        if "vision" in self.model:
            images_messages = [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{encode_image(pil_image=image)}"}
                }
                for image in images
            ]
            text_message = {
                "type": "text",
                "text": input_body
            }
            message = [text_message] + images_messages

            response = self.client.chat.completions.create(
                model=self.model,
                seed=self.seed,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": message}
                ]
            )
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                seed=self.seed,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": input_body}
                ]
            )
        out = response.choices[0].message.content
        return out


class ClaudeClient(LLMClient):
    def __init__(self, model):
        super(ClaudeClient, self).__init__()
        self.client = anthropic.Anthropic()
        self.model = model

    def send_request(self, prompt, input_body, images, **kwargs):
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
            "text": input_body
        }
        message = images_messages + [text_message]

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            temperature=0.0,
            system=prompt,
            messages=[
                {"role": "user", "content": message}
            ]
        )

        out = response.content[0].text
        return out


class HFTextGenClient(LLMClient):
    def __init__(self, model, server_url):
        super(HFTextGenClient, self).__init__()
        self.model = model
        self.server_url = server_url
        self.client = text_generation.Client(self.server_url, timeout=5000)

    def send_request(self, prompt, input_body, images, **kwargs):
        max_new_tokens = kwargs['max_tokens'] if 'max_tokens' in kwargs else 952
        return self.client.generate(f"{prompt} \n{input_body}", max_new_tokens=max_new_tokens).generated_text


class HFLlava(LLMClient):
    def __init__(self, model, device):
        """
        :param model:
        :param device: 'cuda' or 'cpu'
        """
        super(HFLlava, self).__init__()
        self.device = device

        self.model = LlavaNextForConditionalGeneration.from_pretrained(model)
        self.model.to(self.device)
        logging.info("Loading model completed.")

        logging.info("Loading processor...")
        self.processor = LlavaNextProcessor.from_pretrained(model)
        logging.info("Loading processor completed.")

    def send_request(self, prompt, input_body, images, **kwargs):
        if len(images) > 0:
            image = combine_images(images)
        else:
            image = None

        message = f"{prompt} \n{input_body}"
        message = f"USER: <image>\n{message}ASSISTANT:"

        if image is None:
            # Only needed for llava 1.5
            # blank_image = create_blank_image()
            # inputs = processor(text=prompt, images=blank_image, return_tensors="pt")

            inputs = self.processor(text=message, return_tensors="pt")
        else:
            inputs = self.processor(text=message, images=image, return_tensors="pt")

        inputs = inputs.to(self.device)

        # Generate
        generate_ids = self.model.generate(**inputs, max_length=4096)
        text_from_lava = (
            self.processor.batch_decode(generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
        )
        # "\nUSER: What's the content of the image?\nASSISTANT: The image features a stop sign on a street corner"
        out = str(text_from_lava).split('ASSISTANT:')[-1]

        return out


def create_blank_image():
    # Define the size of the image (width, height)
    width = 500
    height = 300
    # Define the color for the blank image (in RGB format)
    background_color = (0, 0, 0)  # Black color
    # Create a new blank image
    blank_image = Image.new("RGB", (width, height), background_color)
    return blank_image