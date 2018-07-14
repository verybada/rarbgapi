import sys
import logging
import argparse


from .rarbgapi import RarbgAPI


def _show_categories():
    prefix = 'CATEGORY_'
    for name in dir(RarbgAPI):
        if not name.startswith(prefix):
            continue

        category = name.replace(prefix, '')
        index = getattr(RarbgAPI, name)
        print('%s -> %s' % (category, index))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--category-table',
                        help='Get a list of category index',
                        action='store_true')
    parser.add_argument('--search-string', help='Query string')
    parser.add_argument('--sort',
                        choices=['seeders', 'leechers', 'last'],
                        help='How torrents will be sorted')
    parser.add_argument('--limit', type=int, choices=[25, 50, 100],
                        help='How many torrents will return')
    parser.add_argument('--category', type=int, help='The index of category')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='verbose')
    args = parser.parse_args()
    if args.category_table:
        _show_categories()
        return

    if args.verbose:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    client = RarbgAPI()
    torrents = client.search(search_string=args.search_string, sort=args.sort,
                             limit=args.limit, category=args.category)
    for torrent in torrents:
        print("%s(%s) %s" % (torrent.filename, torrent.category,
                             torrent.download))


sys.exit(main())
