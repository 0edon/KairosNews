from newspaper import Article
import newspaper.configuration
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from threading import Lock, Event
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from ratelimit import limits, sleep_and_retry


headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.google.com'
    }

session = requests.Session()
session.mount('https://', HTTPAdapter(pool_connections=15, pool_maxsize=15))
config = newspaper.configuration.Configuration()
config.headers = headers
config.request_timeout = 30
config.language = 'pt'
config.request_session = session  

class ThrottledArticle(Article):
    @sleep_and_retry
    @limits(calls=15, period=3)  # Stay under 400/min Arquivo.pt limit
    def download(self):
        return super().download()

max_workers = 15

filename = "expresso2023 copy"
input_file = os.path.join("data/articles_links/", filename)

with open(input_file, 'r', encoding='utf-8') as file:
    data = json.load(file)

links = [item['Link'] for item in data]

start2 = time.time()

# Progress tracking
processed_count = 0
success_count = 0
failed_count = 0
skipped_links = 0  # Counter for skipped links
max_skipped_links = 10  # Limit for skipped links
total_links = len(links)
progress_lock = Lock()
start_time = time.time()

articles_data = []
remaining_links = []
data_lock = Lock()

stop_event = Event()

def save_partial_progress(processed_count):
    path = "data/articles_partial/"
    os.makedirs(path, exist_ok=True)
    partial_file = f'{path}partial_{filename}_{processed_count}.json'
    with open(partial_file, 'w', encoding='utf-8') as fp:
        json.dump(articles_data, fp, indent=4, ensure_ascii=False)
    print(f"\nPartial progress saved to '{partial_file}'")

def process_article(link, retries=3):
    global processed_count, success_count, failed_count, skipped_links

    # Stop processing if the stop_event is set
    if stop_event.is_set():
        return None

    for attempt in range(retries):
        try:
            # Download and parse the article
            article = ThrottledArticle(link, config=config)
            article.download()
            article.parse()

            # Extract and format the publish date
            timestamp = link.split('/')[5]
            date_part = timestamp[:8]
            formatted_date = datetime.strptime(date_part, "%Y%m%d").strftime("%Y-%m-%d")

            # Prepare article data
            article_data = {
                "url": link,
                "title": article.title,
                "text": article.text,
                "publish_date": formatted_date
            }

            # Update progress
            with progress_lock:
                processed_count += 1
                success_count += 1
                elapsed = time.time() - start_time
                print(
                    f"\rProcessed: {processed_count}/{total_links} | "
                    f"Success: {success_count} | "
                    f"Failed: {failed_count} | "
                    f"Speed: {(success_count + failed_count) / elapsed:.1f} art/s | "
                    f"Time: {elapsed:.1f}s",
                    end='', flush=True
                )

                # Save progress every 5,000 articles
                if processed_count % 5000 == 0:
                    save_partial_progress(processed_count)

            return article_data

        except Exception as e:
            # Log the error and retry
            print(f"\nError processing link {link} (attempt {attempt + 1}/{retries}): {e}")
            time.sleep(2)  # Wait before retrying

    # If all retries fail, mark as failed
    with progress_lock:
        processed_count += 1
        failed_count += 1
        skipped_links += 1
        print(f"\nSkipping link after {retries} attempts: {link}")
    return None


try:
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_article, link): link for link in links}
        for future in as_completed(futures):
            # Stop processing if the stop_event is set
            if stop_event.is_set():
                print("\nStop event triggered. Exiting...")
                break

            link = futures[future]
            try:
                article_data = future.result(timeout=30)  # Timeout after 30 seconds
                if article_data:
                    with data_lock:
                        articles_data.append(article_data)
            except Exception as e:
                with progress_lock:
                    print(f"\nError in future result for {link}: {e}")
                    skipped_links += 1
                    print(f"Skipped links so far: {skipped_links}/{max_skipped_links}")

            # Check if the skipped links limit is reached
            if skipped_links >= max_skipped_links:
                print("\nMaximum skipped links limit reached. Stopping execution...")
                stop_event.set()
                break

        # Collect remaining links that were not processed
        remaining_links = [link for link in links if link not in [futures[future] for future in futures if future.done() and not future.cancelled() and future.exception() is None]]

except Exception as e:
    print(f"\nFatal error in main execution: {e}")
    stop_event.set()

finally:
    print("Shutting down ThreadPoolExecutor...")
    executor.shutdown(wait=True)  # Ensure all threads are terminated
    print("ThreadPoolExecutor shut down.")
    elapsed = time.time() - start_time
    print(f"\n\nFinal Results:")
    print(f"Total processed: {processed_count}")
    print(f"Successfully extracted: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"Skipped links: {skipped_links}")
    print(f"Processing speed: {(success_count + failed_count) / elapsed:.1f} articles/second")
    print(f"Total time elapsed: {elapsed:.2f} seconds")

    path = "data/articles/"
    os.makedirs(path, exist_ok=True)

    # Save successfully scraped articles
    with open(f'{path + filename}', 'w', encoding='utf-8') as fp:
        json.dump(articles_data, fp, indent=4, ensure_ascii=False)

    # Save remaining unscraped links only if there are any
    if len(remaining_links) > 0:
        remaining_links_file = f'{path}remaining_{filename}'
        with open(remaining_links_file, 'w', encoding='utf-8') as fp:
            json.dump(remaining_links, fp, indent=4, ensure_ascii=False)
        print(f"Remaining unscraped links saved to '{remaining_links_file}'")
    else:
        print("No remaining unscraped links to save.")