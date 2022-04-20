# rarbgapi

This is a python3 wrapper for RARBG.to.

The api object will automatically fetch/refresh the token and take care rate control (1 request/2 seconds)

## Install
```
pip install rarbgapi
```

## Quickstart

List new torrents

``` python
>>> import rarbgapi
>>> client = rarbgapi.RarbgAPI()
>>> for torrent in client.list():
...     print(torrent)
... 
```

The download link can be found in 
``` python
>>> torrent.download
```

Get more torrents, the limit option supports 25, 50, 100 only.
``` python
>>> client.list(limit=100):
```

Search torrents with specific keyword or imdb, tvdb and themoviedb index via `search_imdb`, `search_tvdb` and `search_themoviedb`
``` python
>>> client.search(search_string="walking dead")
```

or specific category
``` python
>>> client.search(search_string="walking dead", categories=[rarbgapi.RarbgAPI.CATEGORY_TV_EPISODES, rarbgapi.RarbgAPI.CATEGORY_TV_EPISODES_UHD])
```

## options
Here are options to configure rarbgapi client


| Name | Description | 
| -------- | -------- |
| retries     | Retry how many times once error happen     | 

``` python
>>> import rarbgapi
>>> options = {'retries': 10}
>>> client = rarbgapi.RarbgAPI(options)
```


### Supported categories
```
CATEGORY_ADULT
CATEGORY_MOVIE_XVID
CATEGORY_MOVIE_XVID_720P
CATEGORY_MOVIE_H264
CATEGORY_MOVIE_H264_1080P
CATEGORY_MOVIE_H264_720P
CATEGORY_MOVIE_H264_3D
CATEGORY_MOVIE_H264_4K
CATEGORY_MOVIE_H265_4K
CATEGORY_MOVIE_H265_4K_HDR
CATEGORY_MOVIE_FULL_BD
CATEGORY_MOVIE_BD_REMUX
CATEGORY_TV_EPISODES
CATEGORY_TV_EPISODES_HD
CATEGORY_TV_EPISODES_UHD
CATEGORY_MUSIC_MP3
CATEGORY_MUSIC_FLAC
CATEGORY_GAMES_PC_ISO
CATEGORY_GAMES_PC_RIP
CATEGORY_GAMES_PS3
CATEGORY_GAMES_PS4
CATEGORY_GAMES_XBOX
CATEGORY_SOFTWARE
CATEGORY_EBOOK
```
