import sys
sys.path.append(r'c:\Users\Tese\Vscode\Scraping')  # Add the root folder to the Python path

from NewsArticles import getNewsArticles
from PastURLs import getPastURLs

filename ="sapo"
year = 2023

pastURLs = getPastURLs(year=year, newspaper_url='https://sapo.pt', startMonth='01', endMonth='12', filename=filename)

getNewsArticles(year=year,pastURLs=pastURLs, news_htmlTag='article',
                   news_htmlClass='article', links_htmlTag='a', links_htmlClass='', filename=filename, debug=True)

