import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_API_BASE")

async def generate_images(prompt, num_images=1, furry_model=False):
    model_list = ["sdxl", "sdxl", "sdxl", "stable-diffusion-2.1", "kandinsky-2.2", "stable-diffusion-1.5"]
    urls = []
    for model in model_list:
        try:
            # Try to generate an image with the current model
            image_response = openai.Image.create(
                model=model,
                prompt=prompt,
                n=num_images,  # images count
                response_format="url"
            )
            
            for entry in image_response["data"]:
                urls.append(entry["url"])
            
            print(f"Images generated with model {model}")
            return urls, image_response  # Successfully generated images, so return the URLs
        except (openai.error.InvalidRequestError, openai.error.PermissionError) as e:
            print(f"An error occurred while using model {model}: {str(e)}")
            continue  # Skip to the next iteration and try with the next model
    
    return None, "Unable to generate images with any model"  # Return an error if no models work
