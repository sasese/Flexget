from __future__ import unicode_literals, division, absolute_import
import logging

from flexget import plugin
from flexget.event import event

log = logging.getLogger('!! cleanup_input !!')
log.verbose('!! cleanup_input !!') 

# AUTO-RUN CODE
    # Set priority to run plugin as the last in metainfo
        # @plugin.priority(?)
        # def on_task_filter(self, task, config):

def CleanupInput():
# SITUATION
    # Metainfo plugins have created fields.

# OPTIONS
    # 'group' (no, quality, release)
    # Primary function, which sorts individual entries into group entries by:
    # (general) quality, such as:
        # entry: Birdwatcher Vigilante S01E01 HDTV x264
            # (Birdwatching Vigilante S01E01 HDTV x264 - LOL)
            # URL 1: rapidgator.com/files/abc...
            # URL 2: rapidgator.com/files/def...
            # URL 3: netload.in/etc...
            # (Birdwatching Vigilante S01E01 HDTV x264 - KiLLERS)
            # URL 4: etc...
            # (Birdwatching Vigilante S01E01 HDTV x264 - FQM)
            # etc...
    # or (exact) release, as in:
        # entry: Birdwatching Vigilante S01E01 HDTV x264 - LOL
            # URL 1: rapidgator.com/files/abc...
            # URL 2: rapidgator.com/files/def...
            # URL 3: netload.in/etc...
        # entry: Birdwatching Vigilante S01E01 HDTV x264 - KiLLERS
            # URL 1: etc...
        # entry: Birdwatching Vigilante S01E01 HDTV x264 - FQM
            # etc...
    
    # 'decipher' (to do) (no, guess, strict)
        # Not yet implemented function, intended to obtain the names of files whose
        # URLs are too cryptic to parse, such as uptobox.com/u73he7ehe82 instead of
        # rapidgator.com/abc.../birdwatching.vigilante.s01e01.hdtv.x264.rar, either by
            # guess, using modifications of the RSS and parse_urls plugins to add the
                # name of originating items, thus providing clues, or;
            # strict(ly), parsing an entry's URL directly or querying it via a site's API.
                # As for parsing, oboom and rockfile(?) seem to have the names of the files
                # relatively available in the page source, even when hidden in the browser.
                # A search for the series name, tolerant of periods, may usually find the
                # filename. Some attention would be required to deal discern a potential
                # potential mention of the originating Web page, from a link to the file
                # and redundancy to reduce that or a direct filename to acceptable input.
    
    schema = {
        'type': ['string', 'object'],
        'properties': {
            'group': {'type': 'string'},
            'decipher': {'type': 'string'}
        },
        'required': ['group']
    }

# INITIALIZE
    # Copy task.entries to cleanup.entries
    cleanup.entries = copy.deepcopy(task.entries)
    # Reset task.entries to empty
    task.entries.clear()
    
# MAIN
    # for each entry in cleanup.entries
    for each entry in cleanup.entries
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