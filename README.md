# Export your LiveJournal blog data

Based on [arty-name / livejournal-export](https://github.com/arty-name/livejournal-export).

[Livejournal provides a method to export your posts as 
XML](http://www.livejournal.com/export.bml). However 
this has to be done manually for every month of your blog. 
Also [comments are exported separately](http://www.livejournal.com/developer/exporting.bml).
This tool makes exporting more convenient.

You will need Python 3 to use it.

## export.py

This script will do the exporting. Run it after you 
have provided cookies and years as described below.
You will end up with full blog contents in several 
formats. `posts-html` folder will contain basic HTML
of posts and comments. `posts-markdown` will contain
posts in Markdown format with HTML comments and metadata 
necessary to [generate a static blog with Pelican](http://docs.getpelican.com/).
`posts-json` will contain posts with nested comments 
in JSON format should you want to process them further.

## config.json

Edit this file to specify:

- Your LiveJournal login details
- Whether to download posts and comments (Set to `False` to skip the downloading
  step and go directly to the processing of already downloaded data.)
- The range of years you want to download
- Which formats to export

## auth.py

This reads the config file and does the login to Livejournal.

## download_posts.py

This script will download your posts in XML into `posts-xml`
folder. Also it will create `posts-json/all.json` file with all 
the same data in JSON format for convenient processing.

## download_comments.py

This script will download comments from your blog as `comments-xml/*.xml`
files. Also it will create `comments-json/all.json` with all the 
comments data in JSON format for convenient processing.

## Requirements

* `html2text`
* `markdown`
* `BeautifulSoup`
* `requests`

