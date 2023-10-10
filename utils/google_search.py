import json
import cachetools
from googleapiclient.discovery import build
from utils.scrape_web_page import scrape_web_page

google_cache = cachetools.TTLCache(maxsize=100, ttl=3600*60*24)

def google_search(search_term, api_key, cse_id, num_results=5, **kwargs):
    cache_key = (search_term, num_results)
    if cache_key in google_cache:
        print("(debug) Using cached Google search results.")
        return google_cache[cache_key]
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, gl="uk", **kwargs).execute()
    search_results = [
        {"title": item["title"], "link": item["link"], "snippet": item["snippet"]}
        for item in res["items"][:num_results]
    ]

    # Scraping first 3 URLs
    for idx, result in enumerate(search_results[:2]):
        scraped_data = scrape_web_page(result["link"])
        if scraped_data:  # If scraped_data is not None or an error message
            sliced_scraped_data = scraped_data[25:350]  # Skip first 25 characters and limit to 350
            search_results[idx]["scraped_content"] = sliced_scraped_data  # Add sliced scraped_data to the result dictionary

    search_results_str = json.dumps(search_results)
    google_cache[cache_key] = search_results_str
    print(
        "(debug) Used Google search. Number of search results: ",
        num_results,
        "with search term: ",
        search_term,
    )
    print(search_results_str)
    return search_results_str