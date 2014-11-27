from __future__ import unicode_literals, division, absolute_import
import logging

from flexget import plugin
from flexget.event import event

log = logging.getLogger('!! cleanup_input !!')
log.verbose('!! cleanup_input !!') 

# AUTO-RUN CODE
    # Set priority to run plugin as the last in meta_input
    # @plugin.priority(175)
    # def on_task_filter(self, task, config):

def CleanupInput(): # options: 'group' (no, quality, release), to do 'decrypt' (no, guess, strict)
# SITUATION
    # Meta_input plugins have created fields.

# INITIALIZE
    # Copy task.entries to cleanup.entries
    # Reset task.entries to empty
    
# MAIN
    # for each entry in cleanup.entries
        # needed? create group.entries
            # needed ? move all instances of entry.series_name and .episode_id from cleanup.entries to group.entries
            # needed ? for each entry in group.entries
            # why not ? move entries from cleanup to task directly?
            # would reducing the scope to series_name and episode_id matches reduce processing? yes. significantly?
                # create task.entries.entry with group.entries.entry.series_name, .episode_id and .group.reqs
                # move all instances of entry.group.reqs from group.entries to task.entries entry.group.reqs
                    # actually, move url and delete entry
                # Exception: in case of no reqs, skip entry

# CONCLUDE
    # Clean-up
        

    @event('plugin.register')
    def register_plugin():
        plugin.register(CleanupInput, 'cleanup_input', api_ver=2)
