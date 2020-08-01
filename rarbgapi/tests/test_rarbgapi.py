import requests
import pytest
import pytest_httpserver

from rarbgapi import RarbgAPI
from rarbgapi.leakybucket import LeakyBucket


DUMMY_APP_ID = 'test_app_id'
DUMMY_TOKEN = 'test_token'


@pytest.fixture
def client(httpserver):
    client = RarbgAPI(**{'retries': 1})
    client._bucket = LeakyBucket(1000)
    client._endpoint = httpserver.url_for("/")
    client._token = DUMMY_TOKEN
    client.APP_ID = DUMMY_APP_ID
    return client


@pytest.fixture
def expected_headers(client):
    return {
        'user-agent': client._get_user_agent(),
    }


@pytest.fixture
def empty_response():
    return {
        'torrent_results': [],
    }


QUERY_STRING_VALUE = 'json'
SUPPORTED_ARGS = [
        'format_', 'sort', 'limit', 'category',
        'search_string', 'search_tvdb', 'search_themoviedb', 'search_imdb',
    ]


@pytest.mark.parametrize('mode', ['list', 'search'])
@pytest.mark.parametrize('supported_arg', SUPPORTED_ARGS)
def test_supported_arg(
        httpserver, client,
        expected_headers, empty_response,
        mode, supported_arg):
    key = input_arg_to_query_string_key(supported_arg)
    httpserver.expect_request(
        "/",
        headers=expected_headers,
        query_string={
            'app_id': DUMMY_APP_ID, 'token': DUMMY_TOKEN,
            'mode': mode, key: QUERY_STRING_VALUE,
        },
        handler_type=pytest_httpserver.httpserver.HandlerType.PERMANENT,
    ).respond_with_json(empty_response)

    func = getattr(client, mode)
    assert func and func(**{supported_arg: QUERY_STRING_VALUE}) == []


@pytest.mark.parametrize('mode', ['list', 'search'])
def test_arg_categories(
        httpserver, client, expected_headers, empty_response, mode):
    httpserver.expect_request(
        "/",
        headers=expected_headers,
        query_string={
            'app_id': DUMMY_APP_ID, 'token': DUMMY_TOKEN,
            'mode': mode, 'category': '1;2;3',
        },
        handler_type=pytest_httpserver.httpserver.HandlerType.PERMANENT,
    ).respond_with_json(empty_response)

    func = getattr(client, mode)
    assert func and func(categories=[1, 2, 3]) == []


def input_arg_to_query_string_key(arg):
    if arg == 'format_':
        return 'format'
    return arg


@pytest.mark.parametrize(
    'mode', ['list', 'search']
)
def test_unsupported_arg(client, mode):
    func = getattr(client, mode)
    with pytest.raises(ValueError):
        func(foo='bar')


@pytest.mark.parametrize(
    'mode', ['list', 'search']
)
@pytest.mark.parametrize('expired_code', [2, 4])
def test_refresh_token(
        httpserver, client, expected_headers, empty_response,
        mode, expired_code):
    token = 'mytoken123'
    httpserver.expect_request(
        "/",
        headers=expected_headers,
        query_string={
            'token': DUMMY_TOKEN, 'app_id': DUMMY_APP_ID, 'mode': mode,
        },
        handler_type=pytest_httpserver.httpserver.HandlerType.ORDERED
    ).respond_with_json({'error_code': expired_code})
    httpserver.expect_request(
        "/",
        headers=expected_headers,
        query_string={'get_token': 'get_token', 'app_id': DUMMY_APP_ID},
        handler_type=pytest_httpserver.httpserver.HandlerType.ORDERED
    ).respond_with_json({'token': token})
    httpserver.expect_request(
        "/",
        headers=expected_headers,
        query_string={
            'token': token, 'app_id': DUMMY_APP_ID, 'mode': mode,
        },
        handler_type=pytest_httpserver.httpserver.HandlerType.ORDERED
    ).respond_with_json(empty_response)

    func = getattr(client, mode)
    assert func and func() == []


@pytest.mark.parametrize(
    'mode', ['list', 'search']
)
def test_empty_error(
        httpserver, client, expected_headers, mode):
    httpserver.expect_request(
        "/",
        headers=expected_headers,
        query_string={
            'token': DUMMY_TOKEN, 'app_id': DUMMY_APP_ID,
            'mode': mode,
        },
        handler_type=pytest_httpserver.httpserver.HandlerType.ONESHOT
    ).respond_with_json({'error_code': 20})

    func = getattr(client, mode)
    assert func and func() == []


@pytest.mark.parametrize(
    'mode', ['list', 'search']
)
def test_throttle_error(
        httpserver, client, expected_headers, empty_response, mode):
    httpserver.expect_request(
        "/",
        headers=expected_headers,
        query_string={
            'token': DUMMY_TOKEN, 'app_id': DUMMY_APP_ID, 'mode': mode,
        },
        handler_type=pytest_httpserver.httpserver.HandlerType.ORDERED
    ).respond_with_json({'error_code': 5})
    httpserver.expect_request(
        "/",
        headers=expected_headers,
        query_string={
            'token': DUMMY_TOKEN, 'app_id': DUMMY_APP_ID, 'mode': mode,
        },
        handler_type=pytest_httpserver.httpserver.HandlerType.ORDERED
    ).respond_with_json(empty_response)

    func = getattr(client, mode)
    assert func and func() == []


@pytest.mark.parametrize(
    'mode', ['list', 'search']
)
def test_retry(
        httpserver, client, expected_headers, empty_response, mode):
    httpserver.expect_request(
        "/",
        headers=expected_headers,
        query_string={
            'token': DUMMY_TOKEN, 'app_id': DUMMY_APP_ID, 'mode': mode,
        },
        handler_type=pytest_httpserver.httpserver.HandlerType.ORDERED
    ).respond_with_json({}, status=500)
    httpserver.expect_request(
        "/",
        headers=expected_headers,
        query_string={
            'token': DUMMY_TOKEN, 'app_id': DUMMY_APP_ID, 'mode': mode,
        },
        handler_type=pytest_httpserver.httpserver.HandlerType.ORDERED
    ).respond_with_json(empty_response)

    client._options['retries'] = 2
    func = getattr(client, mode)
    assert func and func() == []


@pytest.mark.parametrize(
    'mode', ['list', 'search']
)
def test_torrents(
        httpserver, client, expected_headers, mode):
    torrent_json = {
        'filename': 'torrent',
        'category': 'movies/x264',
        'download': 'download_link',
    }
    httpserver.expect_request(
        "/",
        headers=expected_headers,
        query_string={
            'token': DUMMY_TOKEN, 'app_id': DUMMY_APP_ID, 'mode': mode,
        },
        handler_type=pytest_httpserver.httpserver.HandlerType.ORDERED
    ).respond_with_json({
        'torrent_results': [
            torrent_json,
            torrent_json,
        ]
    })
    func = getattr(client, mode)
    torrents = func()
    assert len(torrents) == 2
    for torrent in torrents:
        assert torrent.is_extended is False
        assert torrent.download == 'download_link'
        assert torrent.filename == 'torrent'
        assert torrent.category == 'movies/x264'
        assert torrent.size is None
        assert torrent.pubdate is None
        assert torrent.page is None
        assert torrent.seeders is None
        assert torrent.leechers is None

        with pytest.raises(AttributeError):
            torrent.foobar


@pytest.mark.parametrize(
    'mode', ['list', 'search']
)
def test_extended_torrents(
        httpserver, client, expected_headers, mode):
    torrent_json = {
        "title": "torrent",
        "category": "Movies/x264",
        "download": "download_link",
        "seeders": 12,
        "leechers": 6,
        "size": 504519520,
        "pubdate": "2017-05-21 02:13:49 +0000",
        "episode_info": {
            "imdb": "tt4443856",
            "tvrage": None,
            "tvdb": None,
            "themoviedb": "430293"
        },
        "ranked": 1,
        "info_page": "https://torrentapi.org/...."
    }
    httpserver.expect_request(
        "/",
        headers=expected_headers,
        query_string={
            'token': DUMMY_TOKEN, 'app_id': DUMMY_APP_ID, 'mode': mode,
        },
        handler_type=pytest_httpserver.httpserver.HandlerType.ORDERED
    ).respond_with_json({
        'torrent_results': [
            torrent_json,
            torrent_json,
        ]
    })

    func = getattr(client, mode)
    torrents = func()
    assert len(torrents) == 2
    for torrent in torrents:
        assert torrent.is_extended is True
        assert torrent.download == 'download_link'
        assert torrent.filename == 'torrent'
        assert torrent.category == 'Movies/x264'
        assert torrent.size == 504519520
        assert torrent.pubdate == "2017-05-21 02:13:49 +0000"
        assert torrent.page == "https://torrentapi.org/...."
        assert torrent.seeders == 12
        assert torrent.leechers == 6

        with pytest.raises(AttributeError):
            torrent.foobar
