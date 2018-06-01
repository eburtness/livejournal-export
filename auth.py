#!/usr/bin/env python3
import sys
import json
import requests

# Load config from file
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Attempt login
#
# (Beware that it only takes a few invalid login attempts to get your IP address temporarily banned.)
#
SECRET = {'user': config['USERNAME'], 'password': config['PASSWORD']}
r = requests.post('https://www.livejournal.com/login.bml', data=SECRET)
if not 'Welcome back to LiveJournal!' in r.text:
    sys.exit('Logging into LiveJournal failed. Check username and password in config.json.')

# Save cookies from successful login and set headers
print('\nLogged into LiveJournal as ' + config['USERNAME'] + "...\n")
cookies = r.cookies
headers = {
    'User-Agent': 'https://github.com/arty-name/livejournal-export; me@arty.name',
    'Accept-Language': 'en-US'
}
