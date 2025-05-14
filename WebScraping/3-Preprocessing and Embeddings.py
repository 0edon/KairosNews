import json
import os
import pandas as pd
import re
from sentence_transformers import SentenceTransformer

#Filename of the input file and its path
filename = ""
input_file = os.path.join("", filename)
# Load the pre-trained model for sentence embeddings
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def preprocessing(input_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except UnicodeDecodeError:
        print(f"Error decoding {input_file}. Please ensure the file is encoded in UTF-8.")
        return
    
    # Flatten nested lists of articles
    articles = [item for sublist in data for item in sublist]
    
    initial_count = len(articles)
    # Filter out articles with less than 30 words
    filtered_articles = [article for article in articles if len(article['text'].split()) >= 30]
    print(f'Number of small articles: {initial_count-len(filtered_articles)}')
    
    # Create a DataFrame and remove duplicates
    df = pd.DataFrame(filtered_articles)
    df.drop_duplicates(subset=['text'], keep='first', inplace=True)
    print(f'Number of duplicate articles: {len(filtered_articles)-len(df)}')
    df = df.reset_index(drop=True)
    
    # Clean the 'text' field (remove HTML tags, newlines, and extra spaces)
    df["text"] = df["text"].apply(lambda x: re.sub(r'<[^>]*>', '', x))  # Remove HTML tags
    df["text"] = df["text"].apply(lambda x: re.sub(r'\n+', ' ', x))     # Replace newlines with spaces
    df["text"] = df["text"].apply(lambda x: re.sub(r'\s+', ' ', x).strip())  # Remove extra spaces and strip
    
    # Clean the 'title' field (similar to 'text')
    df["title"] = df["title"].apply(lambda x: re.sub(r'<[^>]*>', '', x)) # Remove HTML tags
    df["title"] = df["title"].apply(lambda x: re.sub(r'\n+', ' ', x))    # Replace newlines with spaces
    df["title"] = df["title"].apply(lambda x: re.sub(r'\s+', ' ', x).strip()) # Remove extra spaces and strip

    filtered_count = len(df)
    
    # Generate embeddings using the pre-trained model
    embeddings = model.encode(df["text"], show_progress_bar=True, batch_size=16, device='cuda:0')
    df.insert(3, "embedding", [embeddings[i].tolist() for i in range(len(embeddings))])

    removed_count = initial_count - filtered_count
    print(f'Number of articles kept: {filtered_count}')
    print(f'Number of articles removed: {removed_count}')

    # Save the filtered and processed articles to a JSON file
    path = "data/articles_done/"
    os.makedirs(path, exist_ok=True)
    df.to_json(f'{path + filename}.json', orient='records', lines=True, force_ascii=False)

# Run the function
preprocessing(input_file)
