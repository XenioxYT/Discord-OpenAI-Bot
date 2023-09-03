import requests
import json
import os
from dotenv import load_dotenv

def query_wolfram_alpha(query):
    load_dotenv()
    api_key = os.getenv("WOLFRAM_ALPHA_API_KEY")
    
    base_url = "http://api.wolframalpha.com/v2/query?"
    params = {
        "input": query,
        "format": "plaintext",  
        "output": "JSON",
        "appid": api_key,
    }
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        filtered_response = filter_relevant_info(response.json())
        return filtered_response
    else:
        return None

def filter_relevant_info(result_json):
    relevant_info = {}
    if 'queryresult' in result_json:
        if 'pods' in result_json['queryresult']:
            for pod in result_json['queryresult']['pods']:
                pod_title = pod.get('title', 'Unknown')
                subpods = pod.get('subpods', [])
                if subpods:
                    relevant_info[pod_title] = subpods[0].get('plaintext', 'No data')
    return json.dumps(relevant_info)  # Convert dict to JSON-formatted string

# Example usage
# result = query_wolfram_alpha("What is the capital of France?")
# print(result)  # This will print a JSON-formatted string
