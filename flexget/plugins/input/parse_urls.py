from __future__ import unicode_literals, division, absolute_import
import logging
import urllib2

from urlparse import urlparse

from flexget import plugin
from flexget.event import event

log = logging.getLogger('!! parse_urls !!')
log.verbose('!! parse_urls !!') 

# AUTO-RUN CODE
    # Set priority to run plugin as the last in meta_input
        # @plugin.priority(?)
        # def on_task_filter(self, task, config):

# SITUATION
    # Input plugins have created task.entries

# INITIALIZE
    # Copy task.entries to parse.entries
    parse.entries = task.entries
    # Reset task.entries
    task.entries.clear()

# MAIN
    # for each entry in parse.entries
    for entry in parse.entries:
        # for each url in entry (entry['url'])
        for url in entry['url']:
        # D:\pp\App\Lib\site-packages\flexget\plugins\filter\magnets.py
        # 18: entry['urls'] = [url for url in entry['urls'] if not url.startswith('magnet:')]
            # parse url into parsed_urls
                # inspect pyload plugin for method
            # for each url in parsed_urls
                # parse name from url
                # create task.entry [name, url]

# CONCLUDE
    # Clean-up
    
def parseURLs(url, accept="all", reject="none"):
    """
    Parses a URL for URLs;
    optionally filters any parsed URLs and;
    returns the results.
    """
    
    try: urllib2.urlopen(req)
    except URLError as e:
        log.error(e.reason)

    @event('plugin.register')
    def register_plugin():
        plugin.register(ParseURLs, 'parse_urls', api_ver=2)
