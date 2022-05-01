#!/usr/bin/env python3

import json
import sys
import os
import subprocess
import re
import html2text
import markdown
from bs4 import BeautifulSoup
from datetime import datetime
from operator import itemgetter

from livejournaldl import LiveJournalDL


TAG = re.compile(r'\[!\[(.*?)\]\(http:\/\/utx.ambience.ru\/img\/.*?\)\]\(.*?\)')
USER = re.compile(r'<lj user="?(.*?)"?>')
TAGLESS_NEWLINES = re.compile('(?<!>)\n')
NEWLINES = re.compile('(\s*\n){3,}')

# Special Markdown characters to escape.
# Not included because I don't think they'll cause an issue:
# '{', '}', '.', '!', '(', ')'
MDCHARS = ['*', '_', '[', ']', '#', '+', '-']

SLUGS = {}


def fix_user_links(json):
    """ replace user links with usernames """
    if 'subject' in json:
        json['subject'] = USER.sub(r'\1', json['subject'])

    if 'body' in json and json['body']:
        json['body'] = USER.sub(r'\1', json['body'])


def json_to_html(json):
    if json['body']:
        b = TAGLESS_NEWLINES.sub('<br>\n', json['body'])
    else:
        b = ''

    return """<!doctype html>
<meta charset="utf-8">
<title>{subject}</title>
<article>
<h1>{subject}</h1>
{body}
</article>
""".format(
        subject=json['subject'] or json['date'],
        body=b
    )


def get_slug(json):
    slug = json['subject']
    if not len(slug):
        slug = json['id']

    if '<' in slug or '&' in slug:
        slug = BeautifulSoup('<p>{0}</p>'.format(slug)).text

    slug = re.compile(r'\W+').sub('-', slug)
    slug = re.compile(r'^-|-$').sub('', slug)

    if slug in SLUGS:
        slug += (len(slug) and '-' or '') + json['id']

    SLUGS[slug] = True

    return slug


def json_to_markdown(json):
    if json['body']:
        body = TAGLESS_NEWLINES.sub('<br>', json['body'])
    else:
        body = ''

    h = html2text.HTML2Text()
    h.body_width = 0
    h.unicode_snob = True
    body = h.handle(body)
    body = NEWLINES.sub('\n\n', body)

    # read UTX tags
    tags = TAG.findall(body)
    json['tags'] = len(tags) and '\ntags: {0}'.format(', '.join(tags)) or ''

    # remove UTX tags from text
    json['body'] = TAG.sub('', body).strip()

    json['slug'] = get_slug(json)
    json['subject'] = json['subject'] or json['date']

    return """id: {id}
title: {subject}
slug: {slug}
date: {date}{tags}

{body}
""".format(**json)


# Converts to markdown formatted for Day One
def json_to_dayone(json):
    if json['body']:
        body = TAGLESS_NEWLINES.sub('<br>', json['body'])
    else:
        body = ''

    h = html2text.HTML2Text()
    h.body_width = 0
    h.unicode_snob = True
    body = h.handle(body)
    body = NEWLINES.sub('\n\n', body)

    # read UTX tags
    tags = TAG.findall(body)
    json['tags'] = len(tags) and '\ntags: {0}'.format(', '.join(tags)) or ''

    # remove UTX tags from text
    json['body'] = TAG.sub('', body).strip()

    json['slug'] = get_slug(json)
    json['subject'] = json['subject'] or json['date']

    return """# {subject}

{body}
""".format(**json)


def group_comments_by_post(comments):
    posts = {}

    for comment in comments:
        post_id = comment['jitemid']

        if post_id not in posts:
            posts[post_id] = {}

        post = posts[post_id]
        post[comment['id']] = comment

    return posts


def nest_comments(comments):
    post = []

    for comment in comments.values():
        fix_user_links(comment)

        if 'parentid' not in comment:
            post.append(comment)
        else:
            comments[comment['parentid']]['children'].append(comment)

    return post


def comment_to_li(comment):
    if 'state' in comment and comment['state'] == 'D':
        return ''

    html = '<h3>{0}: {1}</h3>'.format(comment.get('author', 'anonym'), comment.get('subject', ''))
    html += '\n<a id="comment-{0}"></a>'.format(comment['id'])

    if 'body' in comment:
        html += '\n' + markdown.markdown(TAGLESS_NEWLINES.sub('<br>\n', comment['body']))

    if len(comment['children']) > 0:
        html += '\n' + comments_to_html(comment['children'])

    subject_class = 'subject' in comment and ' class=subject' or ''
    return '<li{0}>{1}\n</li>'.format(subject_class, html)


def comments_to_html(comments):
    return '<ul>\n{0}\n</ul>'.format('\n'.join(map(comment_to_li, sorted(comments, key=itemgetter('id')))))


# Format comments for Day One export
def comment_to_dayone(comment):
    if 'state' in comment and comment['state'] == 'D':
        return ''

    md = ''

    if 'author' in comment:
        md += '> **[{0}](https://{0}.livejournal.com/)**\n'.format(comment['author'])
    else:
        md += '> _anonymous_\n'

    if 'subject' in comment:
        md += '> **{0}**\n'.format(comment['subject'])

    md += '> \n'

    if 'body' in comment:
        b = comment['body']
        # Escape markdown special characters
        for c in MDCHARS:
            if c in b:
                b = b.replace(c, "\\" + c)
        md += '> ' + '> '.join(b.splitlines(True)) + '\n'

    # If this comment has children, process them recursively
    if len(comment['children']) > 0:
        md += '>' + '>'.join(comments_to_dayone(comment['children']).splitlines(True)) + '\n'

    return md


# Format comments for Day One export
def comments_to_dayone(comments):
    return '\n{0}'.format('\n'.join(map(comment_to_dayone, sorted(comments, key=itemgetter('id')))))


def save_as_json(id, json_post, post_comments):
    json_data = {'id': id, 'post': json_post, 'comments': post_comments}
    with open('posts-json/{0}.json'.format(id), 'w', encoding='utf-8') as f:
        f.write(json.dumps(json_data, ensure_ascii=False, indent=2))


def save_as_html(id, subfolder, json_post, post_comments_html):
    os.makedirs('posts-html/{0}'.format(subfolder), exist_ok=True)
    with open('posts-html/{0}/{1}.html'.format(subfolder, id), 'w', encoding='utf-8') as f:
        f.writelines(json_to_html(json_post))
        if post_comments_html:
            f.write('\n<h2>Comments</h2>\n' + post_comments_html)


def save_as_markdown(id, subfolder, json_post, post_comments_html):
    os.makedirs('posts-markdown/{0}'.format(subfolder), exist_ok=True)
    with open('posts-markdown/{0}/{1}.md'.format(subfolder, id), 'w', encoding='utf-8') as f:
        f.write(json_to_markdown(json_post))
    if post_comments_html:
        with open('comments-markdown/{0}.md'.format(json_post['slug']), 'w', encoding='utf-8') as f:
            f.write(post_comments_html)


# Added by Erick for Day One format
def save_as_dayone(id, subfolder, json_post, post_comments):
    os.makedirs('posts-dayone/{0}'.format(subfolder), exist_ok=True)

    with open('posts-dayone/{0}/{1}.md'.format(subfolder, id), 'w', encoding='utf-8') as f:
        # Write out to text file
        f.write(json_to_dayone(json_post))
        if post_comments:
            f.write('\n\n')
            f.write(post_comments)

    # Send to Day One
    tags = []
    if config.get('DAYONE_TAGS'):
        tags += config.get('DAYONE_TAGS').split(' ')
    if json_post.get('mood'):
        tags.append(json_post.get('mood'))
    cmd = [
        config['DAYONE_CMD'],
        '--date="{0}"'.format(json_post['eventtime']),
        '--journal', config['DAYONE_JOURNAL']
    ]
    if tags:
        cmd.append('--tags')
        cmd += tags
        cmd.append('--')
    cmd.append('new')

    with open('posts-dayone/{0}/{1}.md'.format(subfolder, id), 'r', encoding='utf-8') as f:
        out = subprocess.check_output(cmd, stdin=f)
        print('Day One: ' + out.decode().strip())



def load_from_json(file):
    try:
        f = open(file, 'r', encoding='utf-8')
    except IOError as err:
        print("\nError opening file: {0}".format(err))
        sys.exit('Failed to find data. Exiting.')
    else:
        print('Loading from file: ' + file + "\n")
        with f:
            return json.load(f)


def combine(all_posts, all_comments):

    posts_comments = group_comments_by_post(all_comments)

    for json_post in all_posts:
        id = json_post['id']
        jitemid = int(id) >> 8

        date = datetime.strptime(json_post['date'], '%Y-%m-%d %H:%M:%S')
        subfolder = '{0.year}-{0.month:02d}'.format(date)

        post_comments = jitemid in posts_comments and nest_comments(posts_comments[jitemid]) or None
        post_comments_html = post_comments and comments_to_html(post_comments) or ''
        post_comments_dayone = post_comments and comments_to_dayone(post_comments) or ''

        fix_user_links(json_post)

        if config['EXPORT_JSON']:
            save_as_json(id, json_post, post_comments)

        if config['EXPORT_HTML']:
            os.makedirs('posts-html', exist_ok=True)
            save_as_html(id, subfolder, json_post, post_comments_html)

        if config['EXPORT_MARKDOWN']:
            os.makedirs('posts-markdown', exist_ok=True)
            os.makedirs('comments-markdown', exist_ok=True)
            save_as_markdown(id, subfolder, json_post, post_comments_html)

        if config['EXPORT_DAYONE']:
            os.makedirs('posts-dayone', exist_ok=True)
            save_as_dayone(id, subfolder, json_post, post_comments_dayone)



if __name__ == '__main__':

    # Load config from file
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    if config['GET_POSTS'] or config['GET_COMMENTS']:
        # Log in to LiveJournal
        lj = LiveJournalDL()
        if lj.login(config['USERNAME'], config['PASSWORD']):
            print('\nLogged into LiveJournal as ' + config['USERNAME'] + "...\n")
        else:
            sys.exit('Logging into LiveJournal failed. Check username and password in config.json.')

    if config['GET_POSTS']:
        all_posts = lj.download_posts(config['BEGIN_YEAR'], config['END_YEAR'])
    else:
        all_posts = load_from_json('posts-json/all.json')

    if config['GET_COMMENTS']:
        all_comments = lj.download_comments()
    else:
        all_comments = load_from_json('comments-json/all.json')

    combine(all_posts, all_comments)
