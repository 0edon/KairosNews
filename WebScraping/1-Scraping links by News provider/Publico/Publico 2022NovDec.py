import sys
sys.path.append(r'c:\Users\Tese\Vscode\Scraping')  # Add the root folder to the Python path

from NewsArticles import getNewsArticles
from PastURLs import getPastURLs

filename ="publicoNovDec"
year = 2022

pastURLs = getPastURLs(year=year, newspaper_url='https://publico.pt/', startMonth='11', endMonth='12', filename=filename)

getNewsArticles(year=year, pastURLs=pastURLs, news_htmlTag='div', 
                news_htmlClass='article__inner', links_htmlTag='a', links_htmlClass='', filename=filename, debug=True)
