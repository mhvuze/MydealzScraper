# MydealzScraper
Scraper for mydealz.de that also offers bot functionalities for Telegram. Not affiliated with MyDealz in any way. Uses parts from [mydealz_alert](https://github.com/pfannkuchengesicht/mydealz_alert/).

## Requirements
Install the following libraries to use this script:
* bs4
* colorama
* emoji
* lxml
* pyshortener
* maybe more that are not part of Python by default

## Usage
You can control the following settings in `settings.txt`:
* debug_mode: Enable/disable debug messages
* short_url: Enable/disable short urls for deal messages
* max_pages: Set amount of pages that should be scraped per cycle (depending on sleep time, I recommend 1 or 2)
* sleep_time: Set time to sleep after each cycle
* telegram: Enable/disable Telegram messages for new deals
* tg_token: Set token of your Telegram bot
* tg_timeout: Set timeout for Telegram command listening before continuing cycle
* tg_cid: Set recipient chat id on Telegram
* tg_cid2: Set second recipient chat id on Telegram

You can use the following commands on Telegram:
* /add <item>: Add item to list of wanted products
* /remove <item>: Remove item from list of wanted products
* /list: Show list of all wanted products
* /reset: Reset list of discovered deals
* /chatid: Reply with Telegram chat id
* /hello: Ask for life sign without changing anything

## Example image
![alt tag](http://i.imgur.com/lqvXopr.png)

## Todo
* Implement Telegram in a better way, currently the listener just dies at some point, script restart fixes it though
