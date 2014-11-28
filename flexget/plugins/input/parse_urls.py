from __future__ import unicode_literals, division, absolute_import
import logging

from flexget import plugin
from flexget.event import event

log = logging.getLogger('!! parse_urls !!')
log.verbose('!! parse_urls !!') 

# AUTO-RUN CODE
    # Set priority to run plugin as the last in input
    # @plugin.priority(?)
    # def on_task_filter(self, task, config):

def ParseURLs(): # options: none, for now
# SITUATION
    # Input plugins have created task.entries

# INITIALIZE
    # Copy task.entries to parse.entries
    parse.entries = copy.deepcopy(task.entries)
    # Reset task.entries to empty
    task.entries.clear()
    
# MAIN
    for each entry in parse.entries
        # for each url in entry
            # parse url into parsed_urls
            # for each url in parsed_urls
                # parse name from url
                # create task.entry [name, url]

# CONCLUDE
    # Clean-up
        

    @event('plugin.register')
    def register_plugin():
        plugin.register(ParseURLs, 'parse_urls', api_ver=2)
