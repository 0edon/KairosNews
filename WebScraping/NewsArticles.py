"""
NewsArticles modified implementation
Source: https://github.com/diogocorreia01/PublicNewsArchive
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

def getNewsArticles(year, pastURLs, news_htmlTag, news_htmlClass, links_htmlTag, links_htmlClass, filename, debug=True, max_workers=10):
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.google.com'
    }
    
    journalurl = pastURLs[0]
    journalurl_slash_index = pastURLs[0].rfind('/https')
    journalurl = journalurl[journalurl_slash_index + 1:]

    dictOfTags = {'Link': [links_htmlTag, links_htmlClass]}

    # Thread-safe shared resources
    ListOfContents = []
    contents_lock = Lock()
    ListOfBadContents = []
    bad_lock = Lock()
    processed_links = set()
    links_lock = Lock()
    
    # Progress tracking
    processed_count = 0
    progress_lock = Lock()
    total_urls = len(pastURLs)
    start_time = time.time()

    def process_single_url(url):
        nonlocal ListOfContents, ListOfBadContents, processed_count
        try:
            # Process main page
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            if len(response.history) > 5:
                raise requests.exceptions.TooManyRedirects
                
            soup = BeautifulSoup(response.content, 'html.parser', from_encoding="UTF-8")
            ListOfTagContents = soup.find_all(news_htmlTag, class_=news_htmlClass)
            
            for content in ListOfTagContents:
                try:
                    dictOfFeatures = {'JournalURL': journalurl}
                    
                    # Extract link
                    link = content.find(dictOfTags['Link'][0], class_=dictOfTags['Link'][1]).get("href").strip()
                    if link.startswith('/noFrame/replay/'):
                        link = link.replace('/noFrame/replay/', 'https://arquivo.pt/noFrame/replay/')
                    
                    # Check for duplicates
                    with links_lock:
                        if link in processed_links:
                            continue
                        processed_links.add(link)
                    
                    # Verify link
                    article_response = requests.get(link, headers=headers, timeout=10, allow_redirects=True)
                    if article_response.status_code == 200:
                        dictOfFeatures['Link'] = link
                        with contents_lock:
                            ListOfContents.append(dictOfFeatures)
                    else:
                        with bad_lock:
                            ListOfBadContents.append(link)
                            
                except Exception as e:
                    with bad_lock:
                        ListOfBadContents.append(f"Content error: {str(e)}")
                    continue
            
            # Update progress
            with progress_lock:
                processed_count += 1
                elapsed = time.time() - start_time
                articles_per_sec = (len(ListOfContents)+len(ListOfBadContents)) / elapsed if elapsed > 0 else 0
                print(
                    f"\rProcessed {processed_count}/{total_urls} pages "
                    f"({100 * processed_count/total_urls:.1f}%) | "
                    f"Found {len(ListOfContents)} good articles | "
                    f"Speed: {articles_per_sec:.1f} art/s | "
                    f"Bad: {len(ListOfBadContents)}", 
                    end='', flush=True
                )
                    
        except Exception as e:
            with bad_lock:
                ListOfBadContents.append(f"URL error {url}: {str(e)}")
            with progress_lock:
                processed_count += 1

    print(f"Starting processing of {total_urls} pages with {max_workers} workers...")
    start_time = time.time()
    
    # Process URLs in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_single_url, url) for url in pastURLs]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                if debug:
                    print(f"\nThread error: {str(e)}")

    # Final report
    elapsed = time.time() - start_time
    print(f"\n\nFinished in {elapsed:.1f} seconds")
    print(f"Total articles: {len(ListOfContents)+len(ListOfBadContents)}")
    print(f"Bad entries: {len(ListOfBadContents)}")
    print(f"Processing speed: {(len(ListOfContents)+len(ListOfBadContents))/elapsed:.1f} articles/second")

    # Save results
    year = str(year)
    path = "data/"
    path2 = "data/trash/"
    bad_articles_filename = "bad_" + filename + year

    if not os.path.exists(path):
        os.makedirs(path)

    with open(f'{path + filename + year}', 'w', encoding='utf-8') as fp:
        json.dump(ListOfContents, fp, indent=4, ensure_ascii=False)
    
    with open(f'{path2 + bad_articles_filename}', 'w', encoding='utf-8') as fp:
        json.dump(ListOfBadContents, fp, indent=4, ensure_ascii=False)