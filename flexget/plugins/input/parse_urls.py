from __future__ import unicode_literals, division, absolute_import
import logging
import urllib2

from urlparse import urlparse

from flexget import plugin
from flexget.event import event

log = logging.getLogger('!! parse_urls !!')
log.verbose('!! parse_urls !!') 

# SITUATION
    # Input plugins have created task.entries

# AUTO-RUN CODE
    # Set priority to run plugin as the last in input
        # @plugin.priority(?)
        # def on_task_filter(self, task, config):

# INITIALIZE
    # Copy task.entries to parse.entries
    parse.entries = task.entries
    # Reset task.entries
    task.entries.clear()

# MAIN
    # for each entry in parse.entries
    for entry in parse.entries:
        # for each url in entry (entry['url'])
            # D:\pp\App\Lib\site-packages\flexget\plugins\filter\magnets.py
            # 18: entry['urls'] = [url for url in entry['urls'] if not url.startswith('magnet:')]
        for url in entry['url']:
            # parse url into parsed_urls
            parsed_urls = parseURLs(url)
            # for each url in parsed_urls
            for url in parsed_urls:
                # parse name from url
                # create task.entry [name, url]

# CONCLUDE
    # Clean-up
    
def parseURLs(url, accept="all", reject="none"):
    """
    Parses a URL for URLs;
    optionally filters any parsed URLs;
    removes duplicates and;
    returns the results.
    
    OPTIONS
    'accept' (list)
    Reject all URLs except those matching specified patterns.
    'reject' (list)
    Accept all URLs except those matching specified patterns.
    
    Any urlparse group or combination of groups can be used as a pattern. Examples include:
    example.com, ftp://*.example.com, ftp://, xmbc://, https://example.com/files, ftps://*/files
    Patterns may be specified in config.yaml as (part of) a template.
    """
    
    try: urllib2.urlopen(req)
    except URLError as e:
        log.error(e.reason)

    @event('plugin.register')
    def register_plugin():
        plugin.register(ParseURLs, 'parse_urls', api_ver=2)
