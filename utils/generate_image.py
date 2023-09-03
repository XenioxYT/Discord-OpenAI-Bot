import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_API_BASE")

def generate_images(prompt):
    model_list = ["sdxl", "sdxl", "sdxl", "stable-diffusion-2.1", "kandinsky-2.2", "stable-diffusion-1.5"]
    for model in model_list:
        try:
            # Try to generate an image with the current model
            image_url = openai.Image.create(
                model=model,
                prompt=prompt,
                n=1,  # images count
                response_format="url"
            )
            
            url_string = image_url["data"][0]["url"]
            print(f"Image generated with model {model}")
            return url_string, image_url  # Successfully generated image, so return the URL
        except openai.error.InvalidRequestError or openai.error.PermissionError as e:
            print(f"An error occurred while using model {model}: {str(e)}")
            continue  # Skip to the next iteration and try with the next model
    
    return None, "Unable to generate images with any model"  # Return an error if no models work


# result_url, result_data = generate_images("a person holding a sign saying 'Xeniox'")
# if result_url:
#     print(f"Image generated: {result_url}")
# else:
#     print(f"Error: {result_data}")
