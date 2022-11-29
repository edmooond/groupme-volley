import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def draw_image(image_prompt):

    response = openai.Image.create(
        prompt=image_prompt,  # The thingy to draw
        n=1,  # Number of images
        size="1024x1024"  # Might as well make it pretty
    )

    image_url = response['data'][0]['url']

    return image_url
