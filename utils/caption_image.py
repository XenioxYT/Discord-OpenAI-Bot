import re
import requests

def caption_image(image_data):
    # Replace with the appropriate API URL
    api_url = "http://localhost:2000/caption_image"
    res = requests.post(api_url, files={"image": image_data})
    res_json = res.json()
    extracted_text = res_json["text"]
    caption = res_json["caption"]
    print("(debug) Used image captioning. Caption: ", caption)

    # Remove repeating character sequences like "##oooooooooooooooooooooooooooooooooooooooooooooooo"
    caption = re.sub(r'(.)\1{10,}', '', caption)

    # If such sequence was at the beginning of the caption, it could leave leading white space, remove it
    caption = caption.lstrip()

    # Limit the caption to 100 characters
    # caption = caption[:100]

    return caption, extracted_text
