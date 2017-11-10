# MydealzScraper
Scraper for mydealz.de that also offers bot functionalities for Telegram. Not affiliated with MyDealz in any way. Inspired by [mydealz_alert](https://github.com/pfannkuchengesicht/mydealz_alert/).

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
* sleep_time: Set time to sleep after each cycle
* telegram: Enable/disable Telegram messages for new deals
* tg_token: Set token of your Telegram bot
* tg_cid: Set recipient chat id on Telegram
* tg_cid2: Set second recipient chat id on Telegram

You can use the following commands on Telegram:
* /add <item>: Add item to list of wanted products
* /remove <item>: Remove item from list of wanted products
* /list: Show list of all wanted products
* /reset: Reset list of discovered deals
* /hello: Ask for life sign without changing anything

## Example image
![alt tag](https://i.imgur.com/84OVjaW.jpg)
