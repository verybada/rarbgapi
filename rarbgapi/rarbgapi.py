import time
import logging
import platform

import requests

from .leakybucket import LeakyBucket


class TokenExpireException(Exception):
    pass


class NoResultsException(Exception):
    pass


# pylint: disable=too-many-instance-attributes,too-few-public-methods
class Torrent(object):
    '''
    brief
    {
        "filename":"Off.Piste.2016.iNTERNAL.BDRip.x264-LiBRARiANS",
        "category":"Movies/x264",
        "download":"magnet:..."
    }

    extended
    {
        "title":"Off.Piste.2016.iNTERNAL.BDRip.x264-LiBRARiANS",
        "category":"Movies/x264",
        "download":"magnet:...",
        "seeders":12,
        "leechers":6,
        "size":504519520,
        "pubdate":"2017-05-21 02:13:49 +0000",
        "episode_info":{
            "imdb":"tt4443856",
            "tvrage":null,
            "tvdb":null,
            "themoviedb":"430293"
        },
        "ranked":1,
        "info_page":"https://torrentapi.org/...."
    }
    '''
    def __init__(self, mapping):
        self._raw = mapping
        self.is_extended = 'title' in self._raw
        self.category = self._raw['category']
        self.download = self._raw['download']
        self.filename = self._raw.get('filename') or self._raw.get('title')
        self.size = self._raw.get('size')
        self.pubdate = self._raw.get('pubdate')
        self.page = self._raw.get('info_page')

    def __str__(self):
        return '%s(%s)' % (self.filename, self.category)


def json_hook(dct):
    error_code = dct.get('error_code')
    if error_code in [2, 4]:
        raise TokenExpireException('Token expired')
    if error_code == 20:
        raise NoResultsException('No results found')
    if 'download' in dct:
        return Torrent(dct)
    return dct


class _RarbgAPIv2(object):
    '''
    API reference
    https://torrentapi.org/apidocs_v2.txt
    '''
    ENDPOINT = 'http://torrentapi.org/pubapi_v2.php'
    APP_ID = 'rarbgapi'

    def __init__(self):
        super(_RarbgAPIv2, self).__init__()
        self._endpoint = self.ENDPOINT

    def _get_user_agent(self):
        return '{appid}/0.1.1 ({uname}) python {pyver}'.format(
            appid=self.APP_ID,
            uname='; '.join(platform.uname()),
            pyver=platform.python_version())

    # pylint: disable=no-self-use
    def _requests(self, method, url, params=None):
        if not params:
            params = dict()
        params.update({
            'app_id': self.APP_ID
        })

        headers = {
            'user-agent': self._get_user_agent()
        }
        sess = requests.Session()
        req = requests.Request(method, url, params=params, headers=headers)
        preq = req.prepare()
        resp = sess.send(preq)
        resp.raise_for_status()
        return resp

    def _get_token(self):
        '''
        {"token":"xxxxx"}
        '''
        params = {
            'get_token': 'get_token'
        }
        return self._requests('GET', self._endpoint, params)

    def _query(self, mode, token=None, **kwargs):
        params = {
            'mode': mode,
            'token': token
        }
        for key, value in kwargs.items():
            if key not in ['search_string', 'sort', 'limit',
                           'category', 'format_']:
                raise ValueError('unsupported parameter %s' % key)

            if key == 'format_':
                key = 'format'

            if value is None:
                continue

            params[key] = value

        return self._requests('GET', self._endpoint, params)


def request(func):
    # pylint: disable=protected-access
    def wrapper(self, *args, **kwargs):
        max_retries = retries = self._options['retries']
        while retries > 0:
            try:
                backoff = 2**(max_retries - retries)
                if not self._bucket.acquire(1, timeout=2):
                    raise ValueError('accquire token timeout')

                if not self._token:
                    raise TokenExpireException('Empty token')

                resp = func(self, token=self._token, *args, **kwargs)
                json_ = resp.json(object_hook=json_hook)
                return json_['torrent_results']
            except NoResultsException:
                return []
            except TokenExpireException:
                resp = self._get_token()
                content = resp.json()
                self._token = content['token']
                self._log.debug('token=%s', self._token)
            except Exception as exp:  # pylint: disable=broad-except
                self._log.exception('Unexpected exceptin %s', exp)
                retries -= 1
                if not retries:
                    raise
            else:
                retries -= 1
            finally:
                time.sleep(backoff)

        assert 0, 'Unexpected response'
    return wrapper


class RarbgAPI(_RarbgAPIv2):

    CATEGORY_ADULT = 44
    CATEGORY_MOVIE_XVID = 16
    CATEGORY_MOVIE_XVID_720P = 48
    CATEGORY_MOVIE_H264 = 17
    CATEGORY_MOVIE_H264_1080P = 44
    CATEGORY_MOVIE_H264_720P = 45
    CATEGORY_MOVIE_H264_3D = 47
    CATEGORY_MOVIE_FULL_BD = 42
    CATEGORY_MOVIE_BD_REMUX = 46
    CATEGORY_TV_EPISODES = 18
    CATEGORY_TV_EPISODES_HD = 41
    CATEGORY_TV_EPISODES_UHD = 49
    CATEGORY_MUSIC_MP3 = 23
    CATEGORY_MUSIC_FLAC = 25
    CATEGORY_GAMES_PC_ISO = 27
    CATEGORY_GAMES_PC_RIP = 28
    CATEGORY_GAMES_PS3 = 40
    CATEGORY_GAMES_XBOX = 32
    CATEGORY_SOFTWARE = 33
    CATEGORY_EBOOK = 35

    def __init__(self, **options):
        super(RarbgAPI, self).__init__()
        self._token = None
        self._bucket = LeakyBucket(0.5)
        self._log = logging.getLogger(__name__)
        default_options = {
            'retries': 5,
        }
        if options:
            default_options.update(options)
        self._options = default_options

    @request
    # pylint: disable=too-many-arguments
    def list(self, search_string=None, sort=None, limit=None,
             category=None, format_=None, **kwargs):
        return self._query('list', search_string=search_string, sort=sort,
                           limit=limit, category=category, format_=format_,
                           **kwargs)

    @request
    # pylint: disable=too-many-arguments
    def search(self, search_string=None, sort=None, limit=None,
               category=None, format_=None, **kwargs):
        return self._query('search', search_string=search_string,
                           sort=sort, limit=limit, category=category,
                           format_=format_, **kwargs)
