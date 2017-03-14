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
import threading
import time
import traceback
import urllib.parse
import urllib.request
from contextlib import suppress
from colorama import init, Fore, Back, Style
from emoji import emojize
from pyshorteners import Shortener
from threading import Thread

# Emoji definitions
wave = emojize(":wave:", use_aliases=True)
hot = emojize(":fire:", use_aliases=True)
free = emojize(":free:", use_aliases=True)
wish = emojize(":star:", use_aliases=True)

# Basic stuff
init(autoreset=True) # Colorama
shortener = Shortener('Isgd')
header = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0"}

# Get settings from file
def get_settings():
        global debug_mode; global short_url; global telegram
        global max_pages; global sleep_time; global tg_token
        global tg_url; global tg_timeout; global tg_cid
        global tg_cid2; global tg_updateid

        debug_mode = 0
        short_url = 0
        telegram = 0
        
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
        tg_cid = settings["tg_cid"]
        tg_cid2 = settings["tg_cid2"]
        
        with open("tg_update.txt", "r") as id:
                tg_updateid = id.readline()

get_settings()

# Debug mode
def debug(text):
        if debug_mode:
                print(Fore.YELLOW + "DEBUG: " + text)
        return 0

# Get already found deals from file
def get_found():
        global found_deals
        found_deals = [line.rstrip('\n') for line in open ("./found.txt")]
        #print("Bereits gespeicherte Deals:", len(found_deals))
        global found_deals2
        found_deals2 = [line.rstrip('\n') for line in open ("./found" + str(tg_cid2) + ".txt")]

# Get wanted articles from file
def get_wanted():
        global wanted_articles
        wanted_articles = [line.rstrip('\n') for line in open ("./wanted.txt")]
        print(Fore.CYAN + "User 1: Suche nach Deals für: " + str(wanted_articles).replace("[", "").replace("]", ""))
        global wanted_articles2
        wanted_articles2 = [line.rstrip('\n') for line in open ("./wanted{}.txt".format(tg_cid2))]
        print(Fore.CYAN + "User 2: Suche nach Deals für: " + str(wanted_articles2).replace("[", "").replace("]", ""))

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
        url = tg_url + "getUpdates?timeout={}".format(tg_timeout) # added wait time between cycles
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
                        if chat == tg_cid:
                                addon = ""
                        else:
                                addon = chat
                        with open("./wanted{}.txt".format(addon), "a") as add:
                                add.write(text.replace("/add ", "") + "\n")
                        send_message("Schlagwort wurde der Liste hinzugefügt.", chat)
                        debug("Added item to wanted list for " + str(chat))
                        get_wanted()
                if "/remove" in text:
                        if chat == tg_cid:
                                addon = ""
                        else:
                                addon = chat
                        with open("./wanted{}.txt".format(addon), "r") as list:
                                lines = list.readlines()
                        with open("./wanted{}.txt".format(addon), "w") as remove:
                                for line in lines:
                                        if line.lower() != (text.replace("/remove ", "") + "\n").lower():
                                                remove.write(line)
                        send_message("Schlagwort wurde von der Liste entfernt.", chat)
                        debug("Removed item from wanted list for " + str(chat))
                        get_wanted()
                if "/reset" in text:
                        if chat == tg_cid:
                                addon = ""
                        else:
                                addon = chat
                        open("./found{}.txt".format(addon), "w").close()
                        send_message("Liste der gefundenen Deals wurde geleert.", chat)
                        debug("Reset found list for " + str(chat))
                        get_found()
                if "/list" in text:
                        if chat == tg_cid:
                                send_message("Suche nach Deals für: " + str(wanted_articles).replace("[", "").replace("]", ""), chat)
                        else:
                                send_message("Suche nach Deals für: " + str(wanted_articles2).replace("[", "").replace("]", ""), chat)
                if "/hello" in text:
                        send_message("Hi! " + wave + " Ich bin noch da, keine Sorge.", chat)
                if "/chatid" in text:
                        send_message("Hi! " + wave + " Die ID für diesen Chat lautet: " + str(chat), chat)

# Check Telegram for commands
def telegram_check():
    global tg_updateid
    while True:
            try:
                    updates = get_updates(tg_updateid)
                    if len(updates["result"]) > 0:
                            tg_updateid = get_last_update_id(updates) + 1
                            process_updates(updates)
                    with open("tg_update.txt", "w") as id:
                        id.write(str(tg_updateid))                   
            except:
                    print(Back.RED + datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] Ausnahme während Telegram Check. Warte 60sec."))
                    debug(traceback.format_exc())
                    time.sleep(60)

def mydealz_scraper():
    while True:
            # Scraper Freebies
            try:
                    debug("Scraping freebies")
                    site = "https://www.mydealz.de/freebies-new?page=1"
                    request = urllib.request.Request(site, headers=header)
                    src = urllib.request.urlopen(request, timeout=20).read()
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
                                    timestamp = thread.parent.parent.parent.find(class_=re.compile("mute--text cept-time-label overflow--wrap-off space--h-2")).attrs['datetime']
                                    link = thread.get("href")
                                    if short_url:
                                            try:
                                                    proc_link = shortener.short(link)
                                            except:
                                                    print("Shortener-Service nicht erreichbar. Verwende vollen Link.")
                                                    proc_link = link
                                    else:
                                            proc_link = link
                                    with open("./found.txt", "a") as found:
                                            found.write(dealid + "\n")
                                    get_found()
                                    print("[%s] %s für umsonst: %s" % (gettime(timestamp), re.sub(r'[^\x00-\x7F]+',' ', title), proc_link))
                                    if telegram:
                                            send_message((free + " %s: %s" % (title, proc_link)), tg_cid)
                                            send_message((free + " %s: %s" % (title, proc_link)), tg_cid2)
                                    time.sleep(2) # give short url service some rest
            except:
                    print(Back.RED + datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] Ausnahme während Freebie Scraping. Warte 60sec."))
                    debug(traceback.format_exc())
                    time.sleep(60)

            # Scraper Highlights
            try:
                    debug("Scraping highlights")
                    site = "https://www.mydealz.de/"
                    request = urllib.request.Request(site, headers=header)
                    src = urllib.request.urlopen(request, timeout=20).read()
                    soup = bs.BeautifulSoup(src, 'lxml')
                    time.sleep(3)
                    debug("Finished request")
                    listings = soup.find_all("article", {"id":re.compile("threadCarousel_.*")})
                    if listings is None:
                            print("Keine Listings gefunden. Seite geändert?")
                    for articles in listings:
                            highlights = articles.find_all("img", class_=re.compile("cept-thread-img thread-image imgFrame-img"))
                            for thread in highlights:
                                    dealid = (articles.attrs["id"]).replace("Carousel", "")
                                    if dealid in found_deals:
                                            debug("Deal already found " + dealid)
                                            break
                                    title = thread.attrs['alt']
                                    link = thread.parent.get("href")
                                    if short_url:
                                            try:
                                                    proc_link = shortener.short(link)
                                            except:
                                                    print("Shortener-Service nicht erreichbar. Verwende vollen Link.")
                                                    proc_link = link
                                    else:
                                            proc_link = link
                                    with open("./found.txt", "a") as found:
                                            found.write(dealid + "\n")
                                    get_found()
                                    print("[HOT] %s: %s" % (re.sub(r'[^\x00-\x7F]+',' ', title), proc_link))
                                    if telegram:
                                            send_message((hot + " %s: %s" % (title, proc_link)), tg_cid)
                                            send_message((hot + " %s: %s" % (title, proc_link)), tg_cid2)
                                    time.sleep(2) # give short url service some rest
            except:
                    print(Back.RED + datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] Ausnahme während Highlight Scraping. Warte 60sec."))
                    debug(traceback.format_exc())
                    time.sleep(60)

            # Scraper Wanted
            page_number = 1
            try:
                    while page_number < max_pages+1:
                            debug("Scraping page " + str(page_number))

                            # Request settings
                            site = "https://www.mydealz.de/deals-new?page="+str(page_number)
                            request = urllib.request.Request(site, headers=header)
                            src = urllib.request.urlopen(request, timeout=20).read()
                            soup = bs.BeautifulSoup(src, 'lxml')
                            time.sleep(3)
                            debug("Finished request")

                            # Get listings
                            listings = soup.find_all("article")
                            if listings is None:
                                    print("Keine Listings gefunden. Seite geändert?")

                            for articles in listings:
                                    # user 1
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
                                                    timestamp = thread.parent.parent.parent.find(class_=re.compile("mute--text cept-time-label overflow--wrap-off space--h-2")).attrs['datetime']

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

                                                    # Save deal to prevent duplicate messaging
                                                    with open("./found.txt", "a") as found:
                                                            found.write(dealid + "\n")
                                                    get_found()

                                                    print("[%s] %s für %s Euro: %s" % (gettime(timestamp), re.sub(r'[^\x00-\x7F]+',' ', title), int(price), proc_link))
                                                    if telegram:
                                                            send_message((wish + " %s (%s €): %s" % (title, int(price), proc_link)), tg_cid)
                                                    time.sleep(2) # give short url service some rest
                                    # user 2
                                    for wanted_item in wanted_articles2:
                                            deals = articles.find_all("a", string=re.compile("(?i).*("+wanted_item+").*"), class_=re.compile("cept-tt linkPlain space--r-1 space--v-1"))
                                            for thread in deals:
                                                    # Check if this deal has been found before
                                                    dealid = articles.attrs["id"]
                                                    if dealid in found_deals2:
                                                            debug("Deal already found " + dealid)
                                                            break

                                                    # Get deal info
                                                    title = thread.string
                                                    timestamp = thread.parent.parent.parent.find(class_=re.compile("mute--text overflow--wrap-off space--h-2")).attrs['datetime']

                                                    # Fetch and shorten URL
                                                    link = thread.get("href")
                                                    if short_url:
                                                            try:
                                                                    proc_link = shortener.short(link)
                                                            except:
                                                                    print("Shortener-Service nicht erreichbar. Verwende vollen Link.")
                                                                    proc_link = link
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

                                                    # Save deal to prevent duplicate messaging
                                                    with open("./found{}.txt".format(tg_cid2), "a") as found:
                                                            found.write(dealid + "\n")
                                                    get_found()

                                                    print("[%s] %s für %s Euro: %s" % (gettime(timestamp), re.sub(r'[^\x00-\x7F]+',' ', title), int(price), proc_link))
                                                    if telegram:
                                                            send_message((wish + " %s (%s €): %s" % (title, int(price), proc_link)), tg_cid2)
                                                    time.sleep(2) # give short url service some rest
                            page_number += 1
                    else:
                            # Things to do after every cycle
                            page_number = 1
                            debug("Now sleeping until next cycle")
                            time.sleep(sleep_time)
            except:
                    print(Back.RED + datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] Ausnahme während Wanted Scraping. Warte 60sec."))
                    debug(traceback.format_exc())
                    time.sleep(60)

if __name__=='__main__':
        # Check for required files        
        with suppress(Exception):
                open("./wanted.txt", "x")
        with suppress(Exception):
                open("./found.txt", "x")
        with suppress(Exception):
                open("./wanted{}.txt".format(tg_cid2), "x")
        with suppress(Exception):
                open("./found{}.txt".format(tg_cid2), "x")

        # Initial fetch
        get_wanted()
        get_found()

        debug("After cycle sleep: " + str(sleep_time) + "sec, Telegram long pull: " + str(tg_timeout) + "sec")
        debug("Last Telegram update id " + str(tg_updateid))

        Thread(target = telegram_check).start()
        Thread(target = mydealz_scraper).start()
