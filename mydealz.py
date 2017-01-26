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
import json
import re
import requests
import sys
import time
import urllib.parse
import urllib.request
from colorama import init, Fore, Back, Style
from pyshorteners import Shortener

# Basic stuff
init(autoreset=True) # Colorama
shortener = Shortener('Isgd')
page_number = 1
debug_mode = 0
short_url = 0
telegram = 0
tg_updateid = None
tg_timeout = 60
global header
header = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0"}


# Get settings from file
settings = {}
exec(open("./settings.txt").read(), None, settings)
if settings["debug_mode"]:
        debug_mode = 1
if settings["short_url"]:
        short_url = 1
if settings["telegram"]:
        telegram = 1
max_pages = settings["max_pages"]
sleep_time = settings["sleep_time"]
tg_token = settings["tg_token"]
tg_url = "https://api.telegram.org/bot{}/".format(tg_token)
tg_timeout = settings["tg_timeout"]

# Debug mode
def debug(text):
        if debug_mode:
                print(Fore.YELLOW + "DEBUG: " + text)
        return 0

# Get last telegram update ID
with open("tg_update.txt", "r") as id:
        tg_updateid = id.readline()
debug("Last Telegram update id " + str(tg_updateid))

# Get already found deals from file
def get_found():
        global found_deals
        found_deals = [line.rstrip('\n') for line in open ("./found.txt")]
        print("Bereits gespeicherte Deals:", len(found_deals))

# Get wanted articles from file
def get_wanted():
        global wanted_articles
        wanted_articles = [line.rstrip('\n') for line in open ("./wanted.txt")]
        print(Fore.CYAN + "Suche nach Deals für: " + str(wanted_articles).replace("[", "").replace("]", ""))

# Unix time handler
def gettime(unix):
        time = datetime.datetime.fromtimestamp(int(unix)).strftime('%Y-%m-%d %H:%M:%S')
        return time

# Telegram functions
# mostly from: https://www.codementor.io/garethdwyer/building-a-telegram-bot-using-python-part-1-goi5fncay
def get_url(url):
        response = requests.get(url)
        content = response.content.decode("utf-8")
        return content

def get_json_from_url(url):
        content = get_url(url)
        js = json.loads(content)
        return js

def get_updates(offset=None):
        url = tg_url + "getUpdates?timeout=" + str(tg_timeout) # added wait time between cycles
        if offset:
            url += "&offset={}".format(offset)
        js = get_json_from_url(url)
        return js

def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)

def send_message(text, chat_id):
        text = urllib.parse.quote_plus(text)
        url = tg_url + "sendMessage?text={}&chat_id={}&disable_web_page_preview=true".format(text, chat_id)
        get_url(url)

def process_updates(updates):
        for update in updates["result"]:
                text = update["message"]["text"]
                chat = update["message"]["chat"]["id"]
                if "/add" in text:
                        with open("./wanted.txt", "a") as add:
                                add.write(text.replace("/add ", "") + "\n")
                        send_message("Schlagwort wurde der Liste hinzugefügt.", chat)
                        get_wanted()
                if "/remove" in text:
                        with open("./wanted.txt", "r") as list:
                                lines = list.readlines()
                        with open("./wanted.txt", "w") as remove:
                                for line in lines:
                                        if line.lower() != (text.replace("/remove ", "") + "\n").lower():
                                                remove.write(line)
                        send_message("Schlagwort wurde von der Liste entfernt.", chat)
                        get_wanted()
                if "/reset" in text:
                        open("./found.txt", "w").close()
                        send_message("Liste der gefundenen Deals wurde geleert.", chat)
                        get_found()
                if "/list" in text:
                        send_message("Suche nach Deals für: " + str(wanted_articles).replace("[", "").replace("]", ""), chat)
                if "/hello" in text:
                        send_message("Hi! Ich bin noch da, keine Sorge.", chat)

# Main
debug("Total cycle sleep time: " + str(sleep_time + tg_timeout) + "s")
get_wanted()
get_found()

while True:
    # Check Telegram for commands
    updates = get_updates(tg_updateid)    
    if len(updates["result"]) > 0:
            tg_updateid = get_last_update_id(updates) + 1
            process_updates(updates)
    with open("tg_update.txt", "w") as id:
        id.write(str(tg_updateid))

    # Scraper Freebies
    debug("Scraping freebies")
    site = "https://www.mydealz.de/freebies-new?page=1"
    request = urllib.request.Request(site, headers=header)
    src = urllib.request.urlopen(request).read()
    soup = bs.BeautifulSoup(src, 'lxml')
    time.sleep(3)
    debug("Finished request")
    listings = soup.find_all("article")
    if listings is None:
            print("Keine Listings gefunden. Seite geändert?")
    for articles in listings:
            deals = articles.find_all("a", class_=re.compile("cept-tt linkPlain space--r-1 space--v-1"))
            for thread in deals:                                   
                    dealid = articles.attrs["id"]
                    if dealid in found_deals:
                            debug("Deal already found " + dealid)
                            break
                    title = thread.string
                    timestamp = thread.parent.parent.parent.find(class_=re.compile("mute--text overflow--wrap-off space--h-2")).attrs['datetime']
                    link = thread.get("href")
                    if short_url:
                            proc_link = shortener.short(link)
                    else:
                            proc_link = link
                    print("[%s] %s für umsonst: %s" % (gettime(timestamp), title.replace('€', ''), proc_link))
                    if telegram:
                            send_message(("%s: %s" % (title, proc_link)), 1234) # my chat with the bot
                    with open("./found.txt", "a") as found:
                            found.write(dealid + "\n")
                    time.sleep(2) # give short url service some rest

    # Scraper Wanted
    while page_number < max_pages+1:
            debug("Scraping page " + str(page_number))

            # Request settings
            site = "https://www.mydealz.de/deals-new?page="+str(page_number)            
            request = urllib.request.Request(site, headers=header)
            src = urllib.request.urlopen(request).read()
            soup = bs.BeautifulSoup(src, 'lxml')
            time.sleep(3)
            debug("Finished request")

            # Get listings
            listings = soup.find_all("article")
            if listings is None:
                    print("Keine Listings gefunden. Seite geändert?")

            for articles in listings:
                    for wanted_item in wanted_articles:
                            deals = articles.find_all("a", string=re.compile("(?i).*("+wanted_item+").*"), class_=re.compile("cept-tt linkPlain space--r-1 space--v-1"))
                            for thread in deals:
                                    # Check if this deal has been found before                                    
                                    dealid = articles.attrs["id"]
                                    if dealid in found_deals:
                                            debug("Deal already found " + dealid)
                                            break

                                    # Get deal info
                                    title = thread.string
                                    timestamp = thread.parent.parent.parent.find(class_=re.compile("mute--text overflow--wrap-off space--h-2")).attrs['datetime']

                                    # Fetch and shorten URL
                                    link = thread.get("href")
                                    if short_url:
                                            proc_link = shortener.short(link)
                                    else:
                                            proc_link = link

                                    # Try to fetch price (may fail for freebies)
                                    try:
                                            pricestr = thread.parent.parent.parent.find(class_=re.compile("thread-price")).string.strip()
                                    except:
                                            pricestr = "0"

                                    # Replace Euro sign for processing
                                    if("€" in pricestr):
                                            price = float(pricestr.replace('€', '').replace('.', '').replace(',', '.'))
                                    else:
                                            price = 0

                                    print("[%s] %s für %s Euro: %s" % (gettime(timestamp), title.replace('€', ''), int(price), proc_link))
                                    if telegram:
                                            send_message(("%s (%s €): %s" % (title, int(price), proc_link)), 1234) # my chat with the bot

                                    # Save deal to prevent duplicate messaging
                                    with open("./found.txt", "a") as found:
                                            found.write(dealid + "\n")
                                    time.sleep(2) # give short url service some rest
            page_number += 1
    else:
            # Things to do after every cycle
            page_number = 1
            found_deals = [line.rstrip('\n') for line in open ("./found.txt")]
            debug("Now sleeping until next cycle")
            time.sleep(sleep_time)
