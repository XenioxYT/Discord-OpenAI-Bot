import requests
import json
import cachetools

scrape_cache = cachetools.TTLCache(maxsize=100, ttl=3600*60*24)

def scrape_web_page(url):
    if url in scrape_cache:
        print("(debug) Using cached web page scrape.")
        return scrape_cache[url]  # Return cached scraped data if available

    try:
        # Send the URL to the Node.js server and get the scraped data
        response = requests.post("http://localhost:3000/scrape", json={"url": url})
        response.raise_for_status()  # Raises an HTTPError for bad status codes
    except requests.RequestException as e:
        error_message = f"Failed to scrape the webpage due to an HTTP error: {e}"
        print(f"(debug) {error_message}")
        return error_message

    print("(debug) Scraped web page. response: ", response.status_code)

    try:
        scraped_data = response.json()
    except json.JSONDecodeError:
        error_message = "Failed to decode JSON from the webpage response."
        print(f"(debug) {error_message}")
        return error_message

    # Check if an error occurred
    if "error" in scraped_data:
        print(f"(debug) Error occurred while scraping: {scraped_data['error']}")
        # Create a user-friendly error message
        error_message = f"I'm sorry, but I encountered an error while trying to read the webpage at {url}. The specific error was: {scraped_data['error']}. This might be due to the site being down or having security settings that prevent me from reading it. You might want to try again later or check the site yourself."
        return error_message

    # Limit the length of the scraped text
    scraped_text = scraped_data["data"][0:2000]
    scrape_cache[url] = scraped_text  # Cache the scraped data before returning
    return scraped_text
