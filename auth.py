#!/usr/bin/env python3
import requests

SECRET = {'user': '', 'password': ''}

r = requests.post('https://www.livejournal.com/login.bml', data=SECRET)
cookies = r.cookies

headers = {
    'User-Agent': 'https://github.com/arty-name/livejournal-export; me@arty.name',
    'Accept-Language': 'en-US'
}
