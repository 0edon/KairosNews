import sys
sys.path.append(r'c:\Users\Tese\Vscode\Scraping')  # Add the root folder to the Python path

from NewsArticles import getNewsArticles
from PastURLs import getPastURLs

filename ="publico"
year = 2021

pastURLs = getPastURLs(year=year, newspaper_url='https://publico.pt/', startMonth='01', endMonth='12', filename=filename)

getNewsArticles(year=year, pastURLs=pastURLs, news_htmlTag='div', 
                news_htmlClass='card__inner', links_htmlTag='a', links_htmlClass='card__faux-block-link', filename=filename, debug=True)

