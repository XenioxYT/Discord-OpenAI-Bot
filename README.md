# Discord Bot

This repository contains a Discord bot, developed using Python, Pycord, and the OpenAI API. The bot showcases an array of AI capabilities through its interaction with OpenAI's advanced models.

## Overview

The bot connects to Discord servers and channels, and listens for user messages. Once triggered, it initiates a conversation. 

Key features include:

- Natural language conversations enabled by OpenAI's ChatGPT API
- Image captioning through computer vision APIs
- Verification of user permission levels
- Token counting to prevent exceeding API limits  
- Integration with Google search
- Web scraping capabilities
- Integration with WolframAlpha
- Execution of Python code within a Docker container
- Generation of images from text prompts
- Moderation of messages to filter inappropriate content
- Management of user timezones

## Directory Structure  

```
├── bot.py - Main bot script
├── chat_functions.py - Defines OpenAI chat completion functions
├── prompt.py - Contains helper functions for initiating conversations  
├── strings.py - Contains bot responses and status messages
├── .env - Stores environment variables and API keys (not committed)
├── code_interpreter/ - Docker container for running Python code
│   ├── docker.py - Manages execution of code within Docker
│   ├── Dockerfile - Specifies the Docker container configuration
│   └── requirements.txt - Lists Docker Python dependencies
└── utils/ - Contains utility functions
    ├── check_user_level.py - Verifies Discord user permissions
    ├── counter_tokens_in_conversation.py - Counts tokens in a chat
    ├── exponential_backoff.py - Manages ChatGPT retry logic
    ├── generate_image.py - Generates images with DALL-E 
    ├── get_and_set_timezone.py - Handles user timezone settings
    ├── get_conversation.py - Retrieves conversation context
    ├── google_search.py - Queries the Google search API  
    ├── handle_send_to_discord.py - Sends incremental responses
    ├── image_processing.py - Analyses images with CV APIs    
    ├── moderate_message.py - Filters out inappropriate content
    ├── scrape_web_page.py - Extracts text/data from web pages    
    ├── store_conversation.py - Stores conversation history 
    ├── wolfram_alpha.py - Queries the WolframAlpha API
    └── would_exceed_limit.py - Checks for token count limits
```

## Requirements

### Python Packages  

The bot requires the following key packages:

```
pip install openai tiktoken pycord
```

To install requirements for a specific file: 

```
# For image_processing.py
pip install transformers google-cloud-vision azure-cognitiveservices-vision-computervision 
```

### System Requirements

- Python 3.10
- [Docker](https://docs.docker.com/get-docker/)

The BLIP image captioning model demands substantial resources:

- RAM: 32GB+
- GPU VRAM: 8GB+ 

For optimal performance, GPU acceleration is highly recommended.

## Setup  

### Installation

1. Clone the repository
2. Execute `pip install asyncio jsonlib os-sys random2 regex sqlite3 threading aiofiles pytz aiohttp cachetools discord.py openai tiktoken python-dotenv google-api-python-client`
3. Add your API keys to `.env` 
4. Start the bot by running `python bot.py`    

Trigger the bot by typing "byte".

## Usage

The bot initiates a conversation when it hears "byte" or receives DMs. 

Key commands include:  

- `!clear` - Clears conversation history (in servers, only users with the "Bot Manager" role can run this)
- `!timezone` - Sets your timezone   

Commands exclusive to admins:

- `!unblock` - Allows the bot to respond

## image_processing.py  

This script manages the generation of image captions using various computer vision APIs:

- [Google Cloud Vision](https://cloud.google.com/vision)
- [Azure Computer Vision](https://azure.microsoft.com/en-us/services/cognitive-services/computer-vision/)    
- [BLIP](https://github.com/salesforce/BLIP)

Each API operates in a separate thread to generate multiple captions that are then merged into the final result.  

The `get_detailed_caption` function orchestrates the API calls and combines the results.

Key functionalities include:  

- Image download from URL
- Generation of multiple captions by the BLIP thread   
- Extraction of labels, text, etc. by Google Vision
- Provision of alternate tags and descriptions by Azure Vision 
- Compilation of results into a single object

## Customization

- Modify `strings.py` to add new responses   
- Add API integrations in the `utils/` directory
- Alter moderation rules in `moderate_message.py`
- Substitute image generation models
