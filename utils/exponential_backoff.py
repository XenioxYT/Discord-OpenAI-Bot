import requests
import json
import re
import time
import itertools
import openai

def exponential_backoff(api_call, max_retries=5):
    # Define the list of models inside the function
    models = ["gpt-4", "gpt-4", "gpt-3.5-turbo-16k"]
    model_cycle = itertools.cycle(models)  # create an infinite iterator
    
    delay = 1  # initial delay is 1 second
    
    for i in range(max_retries):
        model = next(model_cycle)  # get the next model from the cycle
        print(f"\033[32mUsing model {model}.\033[0m")
        
        try:
            return api_call(model)
        except (requests.RequestException, Exception, openai.error.OpenAIError, openai.error.InvalidRequestError) as e:
            error_msg = str(e)
            try:
                error_data = json.loads(error_msg)
                if "detail" in error_data:
                    error_detail = error_data["detail"]
                    if "Rate limit reached" in error_detail:
                        wait_time = int(re.findall(r"\d+", error_detail)[0])
                        print(f"Rate limit reached. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
            except json.JSONDecodeError:
                pass
            
            print(f"Error occurred: {e}. Retrying in {delay} seconds...")
            print(f"\033[31m{model} didn't work on attempt {i+1}...\033[0m")
            time.sleep(delay)
            delay *= 2  # double the delay each time
    
    # If we get here, we've exhausted all retries
    raise Exception("API call failed after maximum number of retries with all models")

# # Dummy API call function for testing
# def api_call(model):
#     raise requests.RequestException(f"Some issue with {model}")  # replace this with actual API call

# # Test the function
# try:
#     result = exponential_backoff(api_call)
#     print(f"API call succeeded with result: {result}")
# except Exception as e:
#     print(f"API call failed with error: {e}")
