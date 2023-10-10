functions = [
    {
        "name": "google_search",
        "description": "Use the 'google_search' tool to retrieve internet search results relevant to your input. The results will return links and snippets of text from the webpages",
        "parameters": {
            "type": "object",
            "properties": {
                "search_term": {
                    "type": "string",
                    "description": "The term to search for."
                },
                "num_results": {
                    "type": "integer",
                    "enum": [5, 10, 15],
                    "description": "Number of search results."
                },
            },
            "required": ["search_term"],
        },
    },
    {
        "name": "scrape_web_page",
        "description": "Scrape data from a webpage given a URL. Return it in conversational format.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL of the webpage to scrape."
                },
            },
            "required": ["url"],
        },
    },
    {
        "name": "generate_image",
        "description": "Generate images based on a text prompt. The prompt should be detailed and limited to 25 words. Use when the user asks you to generate, send, give, (and any other synonyms) an image. Craft your input by 'showing' and not 'telling' the imagery.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The text prompt based on which the images will be generated. Craft your input by 'showing' and not 'telling' the imagery. Think in terms of what you'd want to see in a photograph or a painting."
                },
                "num_images": {
                    "type": "integer",
                    "enum": [1, 2, 3, 4],
                    "description": "Number of images to generate. Maximum 4 images."
                },
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "ask_wolfram_alpha",
        "description": "Query Wolfram Alpha and return the results in a conversational format.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to send to Wolfram Alpha."
                },
            },
            "required": ["query"],
        },
    },
    # {
    #   "name": "run_python_code_in_docker",
    #   "description": "Provide Python code to episodically run inside a short-lived Docker container. The environment is ephemeral - no state is retained between executions.",  
    #   "parameters": {
    #     "type": "object",
    #     "properties": {
    #       "code": {
    #         "type": "string",
    #         "description": "Python code to execute. Should use print statements to output data. Define all necessary functions, classes, data loading, and preprocessing inside the provided code since the environment is not persistent across calls. The code should be structured as a single JSON-compatible string, with special characters like newlines properly escaped."
    #       }
    #     },
    #     "required": ["code"]
    #   }
    # }
]
