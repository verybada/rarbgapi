#!/usr/bin/env python

# example: find all "matrix" x264 movies in 720

import rarbgapi

client = rarbgapi.RarbgAPI()
# Note: https://rarbg.com/torrents.php shows 'Movies/x264/720' is category 45
torrents = client.search(search_string='matrix',category=45)
for torrent in torrents:
    print("%s %s %s" % (torrent.filename, torrent.category, torrent.download))
