import base64
from io import BytesIO
from PIL import Image
from PIL import ImageOps
import torch
from transformers import BlipForConditionalGeneration, BlipProcessor
import pytesseract
import cv2
import numpy as np
from flask import Flask, request, jsonify

# Initialize Flask app
app = Flask(__name__)

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {device}")

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large", torch_dtype=torch.float32).to(device)
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

def caption_image(raw_image, num_beams=15):
    print("Processing image")
    inputs = processor(raw_image.convert('RGB'), return_tensors="pt").to(device, torch.float32)
    print(f"Inputs processed, shape: {inputs['pixel_values'].shape}")
    
    print("Generating caption")
    if num_beams is None:
        out = model.generate(**inputs, max_new_tokens=100)
    else:
        out = model.generate(**inputs, max_new_tokens=100, num_beams=num_beams)
    print("Caption generated")
    
    return processor.decode(out[0], skip_special_tokens=True)

def preprocess_for_ocr(img):
    # Convert to gray
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply dilation and erosion to remove some noise
    kernel = np.ones((1, 1), np.uint8)
    img_dilated = cv2.dilate(img_gray, kernel, iterations=1)
    img_eroded = cv2.erode(img_dilated, kernel, iterations=1)

    # Apply threshold to get image with only black and white
    img_thresh = cv2.threshold(img_eroded, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    return img_thresh

def extract_text(image, min_confidence=40):
    print("Extracting text from image")

    # Convert PIL image to OpenCV format
    img_cv = np.array(image) 
    img_cv = img_cv[:, :, ::-1].copy() 

    # Preprocess the image
    img_preprocessed = preprocess_for_ocr(img_cv)

    # Convert the image back to PIL format
    img_preprocessed = Image.fromarray(img_preprocessed)

    # Perform OCR and get confidence
    d = pytesseract.image_to_data(img_preprocessed, config='--psm 6', output_type=pytesseract.Output.DICT)
    filtered_text = ''
    
    for i in range(len(d["text"])):
        if int(d["conf"][i]) >= min_confidence:
            filtered_text += d["text"][i] + " "

    # If there's no valid text detected after filtering by confidence
    if not filtered_text.strip():
        print("No valid text detected after filtering by confidence")
        return "No text detected", None

    print(f"Filtered Text (above {min_confidence} confidence): {filtered_text.strip()}")
    return filtered_text.strip(), None

@app.route("/caption_image", methods=["POST"])
def api_caption_image():
    print("Received POST request")
    data = request.files['image']
    image = Image.open(data.stream)
    print("Opened image from request data")
    
    # Extract text before resizing
    extracted_text, confidence = extract_text(image)
    
    detailed_caption = caption_image(image, num_beams=15)  
    
    if confidence is not None:
        print(f"Caption: {detailed_caption}")
        print(f"Extracted text: {extracted_text} with confidence {confidence:.2f}")
    else:
        print(f"Caption: {detailed_caption}")
        print(f"Extracted text: {extracted_text}")
    
    return jsonify({"caption": detailed_caption, "text": extracted_text})



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2000)