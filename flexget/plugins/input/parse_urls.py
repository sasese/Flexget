from __future__ import unicode_literals, division, absolute_import
import logging

from urlparse import urlparse

from flexget import plugin
from flexget.event import event

urlmatcher = re.compile(r"((https?|ftps?|xdcc|sftp):((//)|(\\\\))+[\w\d:#@%/;$()~_?\+\-=\\\.&]*)", re.IGNORECASE)

log = logging.getLogger('!! parse_urls !!')
log.verbose('!! parse_urls !!') 

# AUTO-RUN CODE
    # Set priority to run plugin as the last in meta_input
        # @plugin.priority(?)
        # def on_task_filter(self, task, config):

def ParseURLs(): # options: none, for now
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
    
def parseURLs(self, html=None, url=None):
    """
    Copied from pyLoad API module's parseURLs
    Parses html content or any arbitaty text for links and returns result of `checkURLs`
    
    :param html: html source
    :return:
    """
    
    urls = []
    
    if html:
        urls += [x[0] for x in urlmatcher.findall(html)]
        
    if url:
        page = getURL(url)
        urls += [x[0] for x in urlmatcher.findall(page)]
        
    # remove duplicates
    return self.checkURLs(set(urls))


    @event('plugin.register')
    def register_plugin():
        plugin.register(ParseURLs, 'parse_urls', api_ver=2)
