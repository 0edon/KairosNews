import sys
sys.path.append(r'c:\Users\Tese\Vscode\Scraping')  # Add the root folder to the Python path

from NewsArticles import getNewsArticles
from PastURLs import getPastURLs

filename ="expressoJanFeb"
year = 2022

pastURLs = getPastURLs(year=year, newspaper_url='https://expresso.pt', startMonth='01', endMonth='02', filename=filename)

getNewsArticles(year=year,pastURLs=pastURLs, news_htmlTag='div',
                   news_htmlClass='entry-text-content', links_htmlTag='a', links_htmlClass='', filename=filename, debug=True)
