import time
import logging
import platform

import requests

from .leakybucket import LeakyBucket
from .__version__ import __version__


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
        self.seeders = self._raw.get('seeders')
        self.leechers = self._raw.get('leechers')

    def __str__(self):
        return f'{self.filename}(self.category)'

    def __getattr__(self, key):
        value = self._raw.get(key)
        if value is None:
            raise AttributeError(f'{key} not exists')
        return value


def json_hook(dct):
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
        super().__init__()
        self._token = None
        self._endpoint = self.ENDPOINT

    def _get_user_agent(self):
        uname = '; '.join(platform.uname())
        pyver = platform.python_version()
        return f'{self.APP_ID}/{__version__} ({uname}) python {pyver}'

    def _get_token(self):
        '''
        {"token":"xxxxx"}
        '''
        params = {
            'get_token': 'get_token'
        }
        return self._requests('GET', self._endpoint, params)

    def _query(self, mode, **kwargs):
        params = {
            'mode': mode,
            'token': self._token
        }

        if 'extended_response' in kwargs:
            params['format'] = 'json_extended' \
                if kwargs['extended_response'] else 'json'
            del kwargs['extended_response']

        if 'categories' in kwargs:
            params['category'] = ';'.join(
                [str(c) for c in kwargs['categories']])
            del kwargs['categories']

        for key, value in kwargs.items():
            if key not in [
                    'sort', 'limit',
                    'search_string', 'search_imdb',
                    'search_tvdb', 'search_themoviedb',
            ]:
                raise ValueError(f'unsupported parameter {key}')

            if value is None:
                continue

            params[key] = value

        return self._requests('GET', self._endpoint, params)

    # pylint: disable=no-self-use
    def _requests(self, method, url, params=None):
        if not params:
            params = {}
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


class TokenExpireException(Exception):
    pass


def request(func):
    # pylint: disable=protected-access, too-many-branches
    def wrapper(self, *args, **kwargs):
        max_retries = retries = self._options['retries']
        while retries > 0:
            try:
                if max_retries != retries:
                    backoff = 2**(max_retries - retries)
                    time.sleep(backoff)

                if not self._bucket.acquire(1, timeout=2):
                    raise ValueError('accquire token timeout')

                if not self._token:
                    raise TokenExpireException('Empty token')

                resp = func(self, *args, **kwargs)
                body = resp.json(object_hook=json_hook)
                error_code = body.get('error_code')
                if error_code:  # pylint: disable=no-else-raise
                    if error_code in [2, 4]:  # pylint: disable=no-else-raise
                        raise TokenExpireException('Token expired')
                    elif error_code == 5:
                        # {
                        #     u'error_code': 5,
                        #     u'error': u'Too many requests per second.
                        #            Maximum requests allowed are 1req/2sec
                        #            Please try again later!'
                        # }
                        self._log.debug('Retry due to throttle')
                        continue
                    elif error_code == 20:
                        return []

                    self._log.warn('error %s', body)
                    raise ValueError('error')
                elif 'torrent_results' not in body:
                    self._log.info('Bad response %s', body)
                return body['torrent_results']
            except ValueError:
                # bad arguments, not necessary to retry
                raise
            except TokenExpireException:
                resp = self._get_token()
                content = resp.json()
                self._token = content['token']
                self._log.debug('token=%s', self._token)
            except Exception as exp:  # pylint: disable=broad-except
                self._log.exception('Unexpected exception %s', exp)
                retries -= 1
                if not retries:
                    raise
            else:
                retries -= 1

        assert 0, 'Unexpected response'
    return wrapper


class RarbgAPI(_RarbgAPIv2):

    CATEGORY_ADULT = 4
    CATEGORY_MOVIE_XVID = 14
    CATEGORY_MOVIE_XVID_720P = 48
    CATEGORY_MOVIE_H264 = 17
    CATEGORY_MOVIE_H264_1080P = 44
    CATEGORY_MOVIE_H264_720P = 45
    CATEGORY_MOVIE_H264_3D = 47
    CATEGORY_MOVIE_H264_4K = 50
    CATEGORY_MOVIE_H265_4K = 51
    CATEGORY_MOVIE_H265_4K_HDR = 52
    CATEGORY_MOVIE_H265_1080P = 54
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
    CATEGORY_GAMES_PS4 = 53
    CATEGORY_GAMES_XBOX = 32
    CATEGORY_SOFTWARE = 33
    CATEGORY_EBOOK = 35

    def __init__(self, **options):
        super().__init__()
        self._bucket = LeakyBucket(0.5)
        self._log = logging.getLogger(__name__)
        default_options = {
            'retries': 5,
        }
        if options:
            default_options.update(options)
        self._options = default_options

    @request
    def list(self, **kwargs):
        """
        List torrents.

        :param sort: (optional) sort torrents, possibile values are
                'seeders', 'leechers' or 'last'
        :param limit: (optional) limit how many torrents will be returned,
                possibile values are 25, 50 or 100
        :param categories: (optional) what kind of torrents should be listed,
                categories should be a list of int
        :param search_string: (optional)
        :param search_imdb: (optional)
        :param search_tvdb: (optional)
        :param search_themoviedb: (optional)
        :param extended_response: (optional) return full context of torrent,
                default is False
        :param category: (optional) DEPRECATED, please use categories instead
        :param format_: (optional) DEPRECATED, please use extended_response
                instead

        :returns: a list of Torrents

        :raises: ValueError
        """
        return self._query('list', **self.backward_compability(kwargs))

    @request
    def search(self, **kwargs):
        """
        Search torrents.

        :param sort: (optional) sort torrents, possibile values are
                'seeders', 'leechers' or 'last'
        :param limit: (optional) limit how many torrents will be returned,
                possibile values are 25, 50 or 100
        :param categories: (optional) what kind of torrents should be
                searched, categories should be a list of int
        :param search_string: (optional)
        :param search_imdb: (optional)
        :param search_tvdb: (optional)
        :param search_themoviedb: (optional)
        :param extended_response: (optional) return full context of torrent,
                default is False
        :param category: (optional) DEPRECATED, please use categories instead
        :param format_: (optional) DEPRECATED, please use extended_response
                instead

        :returns: a list of Torrents

        :raises: ValueError
        """
        return self._query('search', **self.backward_compability(kwargs))

    def backward_compability(self, kwargs):  # pylint: disable=no-self-use
        value = kwargs.pop('format_', None)
        if value:
            kwargs['extended_response'] = (value == 'json_extended')

        value = kwargs.pop('category', None)
        if value:
            kwargs['categories'] = [value, ]

        return kwargs
