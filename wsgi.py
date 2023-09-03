# wsgi.py
from image_to_text_server_blip import app
import os
import sys

sys.path.append(os.getcwd())

if __name__ == "__main__":
    app.run()