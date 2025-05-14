import sys
sys.path.append(r'c:\Users\Tese\Vscode\Scraping')  # Add the root folder to the Python path

from NewsArticles import getNewsArticles
from PastURLs import getPastURLs

filename ="cmjornal"
year = 2023

pastURLs = getPastURLs(year=year, newspaper_url='https://www.cmjornal.pt/', startMonth='01', endMonth='12', filename=filename)

getNewsArticles(year=year, pastURLs=pastURLs, news_htmlTag='div', 
                news_htmlClass='text_container', links_htmlTag='a', links_htmlClass='eventAnalytics', filename=filename, debug=True)

