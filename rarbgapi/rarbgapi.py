import time

import requests

from .leakybucket import LeakyBucket


class TokenExpireException(Exception):
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

    extened
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
    if error_code == 2:
        raise TokenExpireException('Token expired')
    if 'download' in dct:
        return Torrent(dct)
    return dct


class _RarbgAPIv2(object):
    '''
    API reference
    https://torrentapi.org/apidocs_v2.txt
    '''
    ENDPOINT = 'http://torrentapi.org/pubapi_v2.php'

    def __init__(self):
        super(_RarbgAPIv2, self).__init__()
        self._endpoint = self.ENDPOINT

    # pylint: disable=no-self-use
    def _requests(self, method, url, params=None):
        sess = requests.Session()
        req = requests.Request(method, url, params=params)
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
        for key, value in kwargs.iteritems():
            if not key in ['string', 'sort', 'limit', 'category', 'format']:
                raise ValueError('unsupported parameter %s' % key)

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
            except TokenExpireException:
                resp = self._get_token()
                content = resp.json()
                self._token = content['token']
            except Exception:  # pylint: disable=broad-except
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
    def __init__(self, **options):
        super(RarbgAPI, self).__init__()
        self._token = None
        self._bucket = LeakyBucket(0.5)
        default_options = {
            'retries': 5,
        }
        if options:
            default_options.update(options)
        self._options = default_options

    @request
    def list(self, **kwargs):
        return self._query('list', **kwargs)

    @request
    def search(self, **kwargs):
        return self._query('search', **kwargs)
