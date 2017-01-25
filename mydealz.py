#!/usr/bin/python

'''
The MIT License (MIT)
Copyright (c) 2015 Roy Freytag
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import bs4 as bs
import datetime
import re
import sys
import urllib.request
from colorama import init, Fore, Back, Style

# Basic stuff
init(autoreset=True) # Colorama
debug_mode = 1
max_pages = 10
page_number = 1

# Wanted
wanted_articles="Apple"
print("Suche nach Deals für:", wanted_articles) # adapt later for list from file
print("---------------")

# Debug mode
def debug(text):
	if debug_mode:
		print(Fore.YELLOW + "DEBUG: " + text)
	return 0

# Unix time handler
def gettime(unix):
        time = datetime.datetime.fromtimestamp(int(unix)).strftime('%Y-%m-%d %H:%M:%S')
        return time

# Main
while page_number < max_pages+1:

    debug("Scraping page " + str(page_number))
    
    # Request settings
    site = "https://www.mydealz.de/deals-new?page="+str(page_number)
    header = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0"}
    request = urllib.request.Request(site, headers=header)
    src = urllib.request.urlopen(request).read()
    soup = bs.BeautifulSoup(src, 'lxml')

    # Get listings
    listings = soup.find_all("article")
    if listings is None:
        print("Keine Listings gefunden. Seite geändert?")

    for articles in listings:
        deals = articles.find_all("a", string=re.compile("(?i).*("+wanted_articles+").*"), class_=re.compile("cept-tt linkPlain space--r-1 space--v-1"))
        for thread in deals:
            title = thread.string # text also works
            link = thread.get("href")

            # Fetch and convert time
            timestamp = thread.parent.parent.parent.find(class_=re.compile("mute--text overflow--wrap-off space--h-2")).attrs['datetime']
            
            # Try to fetch price (may fail for freebies)
            try:
                pricestr = thread.parent.parent.parent.find(class_=re.compile("thread-price")).string.strip()
            except:
                pricestr="0"

            # Replace Euro sign for processing
            if("€" in pricestr):
                    price = float(pricestr.replace('€', '').replace('.', '').replace(',', '.'))
            else:
                    price = 0

            print("[%s] %s für %s Euro: %s" % (gettime(timestamp), title.replace('€', ''), int(price), link))
            
    page_number += 1

# Debug only
#with open('temp.txt', 'w') as file_:
#    file_.write(str(out2)) #encode("utf-8")
