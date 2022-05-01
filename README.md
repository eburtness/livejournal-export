# Export your LiveJournal blog data

[Livejournal provides a method to export your posts as
XML](http://www.livejournal.com/export.bml). However
this has to be done manually for every month of your blog.
Also [comments are exported separately](http://www.livejournal.com/developer/exporting.bml).
This tool makes exporting more convenient.

This project is a fork of [arty-name / livejournal-export](https://github.com/arty-name/livejournal-export),
with the following additions:

- Logs into LiveJournal with your username and password
  rather than needing cookie data.
- Lets you configure whether to download from LJ or load from
  already-downloaded files, and what formats to export.

## config.json

Edit this file to specify:

- Your LiveJournal login details
- The range of years you want to download
- Whether to download posts and comments or read from already downloaded data.
  (Set to `False` to skip the downloading step and load from the files in
  posts-json and comments-json.)
- Which formats to export

## export.py

This script will do the exporting. Run it after you 
have provided config as described above.
If all options are enabled, you will end up with
full blog contents in several formats. `posts-html`
folder will contain basic HTML of posts and comments.
`posts-markdown` will contain posts in Markdown format
with HTML comments and metadata necessary to
[generate a static blog with Pelican](http://docs.getpelican.com/).
`posts-json` will contain posts with nested comments 
in JSON format should you want to process them further.

## livejournaldl.py — LiveJournalDL class.

`download_posts()` will download your posts in XML into `posts-xml`
folder. Also it will create `posts-json/all.json` file with all 
the same data in JSON format for convenient processing.

`download_comments()` will download comments from your blog as
`comments-xml/*.xml` files. Also it will create `comments-json/all.json`
with all the comments data in JSON format for convenient processing.

## Requirements

Requires Python 3 and the following modules:

* `html2text`
* `markdown`
* `beautifulsoup4`
* `requests`
