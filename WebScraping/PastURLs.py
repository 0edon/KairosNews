"""
PastURLS modified implementation
Source: https://github.com/diogocorreia01/PublicNewsArchive
"""

import requests
import json
from requests.exceptions import Timeout
import time
import os

def getPastURLs(year, newspaper_url, startMonth, endMonth, filename):
    
    start = time.time()
    url_api = 'https://arquivo.pt/textsearch'

    versionHistory = newspaper_url
    maxItems = 5000
    fromDate = f'{year}{startMonth}01000000'
    toDate = f'{year}{endMonth}31235959'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.google.com'
    }
    payload = {
        'versionHistory': versionHistory,
        'maxItems': str(maxItems),
        'from': fromDate,
        'to': toDate,
    }
    mime = "text/html"
    status = 200

    try:
        r = requests.get(url_api, params=payload, headers=headers, timeout=600)
    except Timeout:
        print(f'Timeout has been raised, status code: N/A')
        return []

    content = r.json()
    pastURLs = {}
    skippedItems = []  # List to store skipped items

    for item in content.get('response_items', []):
        # Check for the existence of statusCode and mimeType before accessing
        if 'statusCode' in item and 'mimeType' in item:
            if item['statusCode'] == status and item['mimeType'] == mime:
                # Extract date portion from the timestamp in the URL
                url = item['linkToNoFrame']
                date = url.split('/replay/')[1][:8]  # Get YYYYMMDD

                # Add only the first occurrence of each date
                if date not in pastURLs:
                    pastURLs[date] = url
            else:
                skippedItems.append(item)  # Store the skipped item
        else:
            skippedItems.append(item)  # Store the skipped item
    
    end = time.time()
    
    print(f"Finished processing. Total unique dates found: {len(pastURLs)}, Estimated URLs: {content.get('estimated_nr_results', 'N/A')}, Time elapsed: {end - start:.2f} seconds")

    # Convert the dictionary values to a list to keep only one URL per date
    unique_pastURLs = list(pastURLs.values())

    # Save unique past URLs to a JSON file
    path = "data/trash/"
    year = str(year)
    os.makedirs(path, exist_ok=True)  # Ensure the directory exists
    skipped_filename = "skipped_items_" + filename + year
    past_urls_filename = "past_urls_" + filename + year
    
    with open(f'{path + past_urls_filename}', 'w', encoding='utf-8') as fp:
        json.dump(unique_pastURLs, fp, ensure_ascii=False, indent=4)

    # Save skipped items to a JSON file
    if skippedItems:
        with open(f'{path + skipped_filename}', 'w', encoding='utf-8') as fp:
            json.dump(skippedItems, fp, ensure_ascii=False, indent=4)

    return unique_pastURLs
