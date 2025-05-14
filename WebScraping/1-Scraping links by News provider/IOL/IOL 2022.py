import sys
sys.path.append(r'c:\Users\Tese\Vscode\Scraping')  # Add the root folder to the Python path

from NewsArticles import getNewsArticles
from PastURLs import getPastURLs

filename ="iol"
year = 2022

pastURLs = getPastURLs(year=year, newspaper_url='https://iol.pt/', startMonth='01', endMonth='12', filename=filename)

getNewsArticles(year=year, pastURLs=pastURLs, news_htmlTag='div', 
                news_htmlClass='linkWrapper', links_htmlTag='a', links_htmlClass='link', filename=filename, debug=True)
