#!/usr/bin/env python3
from __future__ import unicode_literals, print_function

import os
import time
import json
import requests
from xml.etree import ElementTree


class LiveJournalDL:
    """Connection to LiveJournal that can fetch posts or comments"""

    def __init__(self):
        self.cookies = {}
        self.headers = {
            'User-Agent': 'https://github.com/Burtness/livejournal-export; 39753627+Burtness@users.noreply.github.com',
            'Accept-Language': 'en-US'
        }

    def login(self, username, password):
        # Attempt login
        #
        # (Beware that it only takes a few invalid login attempts to get your IP address temporarily banned.)
        #
        url = 'https://www.livejournal.com/login.bml'
        r = requests.post(url, data={'user': username, 'password': password}, headers=self.headers)
        if 'Welcome back to LiveJournal!' in r.text:
            # Save cookies from successful login
            self.cookies = r.cookies
            return True
        else:
            # Login failed
            return False

    #
    # Functions for downloading posts
    #

    def download_posts(self, begin_year, end_year):
        years = range(begin_year, end_year + 1)  # first to (last + 1)

        os.makedirs('posts-xml', exist_ok=True)
        os.makedirs('posts-json', exist_ok=True)

        xml_posts = []
        for year in years:
            for month in range(1, 13):
                xml = self.fetch_month_posts(year, month)
                xml_posts.extend(list(ElementTree.fromstring(xml).iter('entry')))

                with open('posts-xml/{0}-{1:02d}.xml'.format(year, month), 'w+', encoding='utf-8') as file:
                    file.write(xml)
                # print('Sleeping 1 sec between months')
                time.sleep(1)
            # print('Sleeping 4 sec between years')
            time.sleep(4)

        json_posts = list(map(self.xml_to_json, xml_posts))
        with open('posts-json/all.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(json_posts, ensure_ascii=False, indent=2))

        return json_posts

    def fetch_month_posts(self, year, month):
        print('Fetching posts {}-{}'.format(year, month))
        response = requests.post(
            'https://www.livejournal.com/export_do.bml',
            headers=self.headers,
            cookies=self.cookies,
            data={
                'what': 'journal',
                'year': year,
                'month': '{0:02d}'.format(month),
                'format': 'xml',
                'header': 'on',
                'encid': '2',
                'field_itemid': 'on',
                'field_eventtime': 'on',
                'field_logtime': 'on',
                'field_subject': 'on',
                'field_event': 'on',
                'field_security': 'on',
                'field_allowmask': 'on',
                'field_currents': 'on'
            }
        )

        return response.text

    @staticmethod
    def xml_to_json(xml):
        def f(field):
            return xml.find(field).text

        return {
            'id': f('itemid'),
            'date': f('logtime'),
            'subject': f('subject') or '',
            'body': f('event'),
            'eventtime': f('eventtime'),
            'security': f('security'),
            'allowmask': f('allowmask'),
            'current_music': f('current_music'),
            'current_mood': f('current_mood')
        }

    #
    # Functions for downloading comments
    #

    def download_comments(self):
        os.makedirs('comments-xml', exist_ok=True)
        os.makedirs('comments-json', exist_ok=True)

        print('Getting comments')

        metadata_xml = self.fetch_xml({'get': 'comment_meta', 'startid': 0})
        with open('comments-xml/comment_meta.xml', 'w', encoding='utf-8') as f:
            f.write(metadata_xml)

        metadata = ElementTree.fromstring(metadata_xml)
        users = self.get_users_map(metadata)

        all_comments = []
        start_id = -1
        max_id = int(metadata.find('maxid').text)
        while start_id < max_id:
            start_id, comments = self.get_more_comments(start_id + 1, users)
            all_comments.extend(comments)
            # print('Sleeping 1 sec between comment batches')
            time.sleep(1)

        with open('comments-json/all.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(all_comments, ensure_ascii=False, indent=2))

        return all_comments

    def get_more_comments(self, start_id, users):
        print('Getting more comments')
        comments = []
        local_max_id = -1

        xml = self.fetch_xml({'get': 'comment_body', 'startid': start_id})
        with open('comments-xml/comment_body-{0}.xml'.format(start_id), 'w', encoding='utf-8') as f:
            f.write(xml)

        for comment_xml in ElementTree.fromstring(xml).iter('comment'):
            comment = {
                'jitemid': int(comment_xml.attrib['jitemid']),
                'id': int(comment_xml.attrib['id']),
                'children': []
            }
            self.get_comment_property('parentid', comment_xml, comment)
            self.get_comment_property('posterid', comment_xml, comment)
            self.get_comment_element('date', comment_xml, comment)
            self.get_comment_element('subject', comment_xml, comment)
            self.get_comment_element('body', comment_xml, comment)

            if 'state' in comment_xml.attrib:
                comment['state'] = comment_xml.attrib['state']

            if 'posterid' in comment:
                comment['author'] = users.get(str(comment['posterid']), "deleted-user")

            local_max_id = max(local_max_id, comment['id'])
            comments.append(comment)

        return local_max_id, comments

    def fetch_xml(self, params):
        response = requests.get(
            'https://www.livejournal.com/export_comments.bml',
            params=params,
            headers=self.headers,
            cookies=self.cookies
        )
        return response.text

    @staticmethod
    def get_users_map(xml):
        print('Fetching users')
        users = {}

        for user in xml.iter('usermap'):
            users[user.attrib['id']] = user.attrib['user']

        with open('comments-json/usermap.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(users, ensure_ascii=False, indent=2))

        return users

    @staticmethod
    def get_comment_property(name, comment_xml, comment):
        if name in comment_xml.attrib:
            comment[name] = int(comment_xml.attrib[name])

    @staticmethod
    def get_comment_element(name, comment_xml, comment):
        elements = comment_xml.findall(name)
        if len(elements) > 0:
            comment[name] = elements[0].text
