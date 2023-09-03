functions = [
    {
        "name": "google_search",
        "description": "Perform a Google search and return the results in a conversational format.",
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
                    "description": "The number of search results to return. Give the results in a conversational format."
                },
            },
            "required": ["search_term"],
        },
    },
    {
        "name": "scrape_web_page",
        "description": "Scrapes data from a webpage given a URL. Return it in conversational format.",
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
        "description": "Generates an image based on a text prompt that you generate. The prompt should be detailed and limited to 25 words.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The text prompt based on which the image will be generated."
                }
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
