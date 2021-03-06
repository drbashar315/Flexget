from __future__ import unicode_literals, division, absolute_import
import logging

from flexget import validator
from flexget.entry import Entry
from flexget.plugin import register_plugin
from flexget.utils import requests, json
from flexget.utils.search import torrent_availability

session = requests.Session()
log = logging.getLogger('search_btn')

# TODO: btn has a limit of 150 searches per hour


class SearchBTN(object):
    def validator(self):
        return validator.factory('text')

    def search(self, entry, config):
        api_key = config

        searches = entry.get('search_strings', [entry['title']])

        if 'series_name' in entry:
            search = {'series': entry['series_name']}
            if 'series_id' in entry:
                search['name'] = entry['series_id']
            searches = [search]

        results = []
        for search in searches:
            data = json.dumps({'method': 'getTorrents', 'params': [api_key, search], 'id': 1})
            try:
                r = session.post('http://api.btnapps.net/', data=data, headers={'Content-type': 'application/json'})
            except requests.RequestException as e:
                log.error('Error searching btn: %s' % e)
                continue
            content = r.json()
            if content['result']['results']:
                for item in content['result']['torrents'].itervalues():
                    if item['Category'] != 'Episode':
                        continue
                    entry = Entry()
                    entry['title'] = item['ReleaseName']
                    entry['url'] = item['DownloadURL']
                    entry['torrent_seeds'] = int(item['Seeders'])
                    entry['torrent_leeches'] = int(item['Leechers'])
                    entry['torrent_info_hash'] = item['InfoHash']
                    entry['search_sort'] = torrent_availability(entry['torrent_seeds'], entry['torrent_leeches'])
                    if item['TvdbID']:
                        entry['tvdb_id'] = int(item['TvdbID'])
                    results.append(entry)
        return results



register_plugin(SearchBTN, 'btn', groups=['search'], debug=True)
