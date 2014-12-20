from __future__ import unicode_literals, division, absolute_import
import logging
import re

from flexget import options, plugin
from flexget.event import event
from flexget.plugin import get_plugin_by_name, PluginError, PluginWarning
from flexget.config_schema import one_or_more
from flexget.utils.cached_input import cached
from flexget.utils.soup import get_soup

log = logging.getLogger('parse_urls')


'''
Notes

General:
This plugin is an assemblage of the discover and html input plugins, parsing candidate entries
provided by input plugins for URLs, filtering those if specified, and creating unified entries
per title attaching the parsed URLs.

To do:
Major: Caching.
       It seems cached_input functions only within a run, and RSS input plugin's all_entries
       mechanism merely rejects candidate entries after encountering the last entry of the
       previous run in the current list. By "injecting" failed entries at that point, or
       appending them at the top of candidates, full parsing of failed and new entries might
       be accomplished. An "injected" candidate would need to be removed from the backlog to
       prevent it being called by any other plugin, as usual.

Considerations:
Major: All other plugins will be unaware of the new values ('parse_urls' and 'parsed_urls').
       Even if existing values were recycled (such as 'url' and 'urls') their altered nature
       would remain unused, without recoding of plugins.
'''


class Parse_URLs(object):
    """
    Parse URLs based on other inputs material.

    Example:

      parse_urls:
        inputs:
          - rss:
              url: http://example.com/feed
              group_links: yes
        links_re:
          - example\.com
        all_entries: no
    """

    schema = {
        'oneOf': [
            {'type': 'object',
                'properties': {
                    'inputs': {'type': 'array', 'items': {
                        'allOf': [{'$ref': '/schema/plugins?phase=input'}, {'maxProperties': 1, 'minProperties': 1}]
                    }},
                    'links_re': one_or_more({'type': 'string'}),
                },
                'additionalProperties': False
             }
        ]
    }

    def __init__(self):
        try:
            self.backlog = plugin.get_plugin_by_name('backlog')
        except plugin.DependencyError:
            log.warning('Unable utilize backlog plugin, entries may slip trough parse_urls in some rare cases')

    def execute_inputs(self, config, task):
        """
        :param config: Parse_URLs config
        :param task: Current task
        :return: List of pseudo entries created by inputs under `inputs` configuration
        """
        entries = []
        entry_titles = set()
        entry_urls = set()

        # Get candidate entries from plugins
        for item in config['inputs']:
            for input_name, input_config in item.iteritems():
                input = get_plugin_by_name(input_name)
                if input.api_ver == 1:
                    raise PluginError('Plugin %s does not support API v2' % input_name)
                method = input.phase_handlers['input']
                try:
                    candidate_entries = method(task, input_config)
                except PluginError as e:
                    log.warning('Error during input plugin %s: %s' % (input_name, e))
                    continue
                if not candidate_entries:
                    log.warning('Input %s did not return anything' % input_name)
                    continue

                cache = task.simple_persistence.get('parse_urls_cache')
                failed = self.backlog.instance.get_injections(task)
#                cache = []

                # For each candidate,
                for entry in candidate_entries:

                    # reject if its index page repeats that in a previous run, unless it failed,
                    if entry['url'] not in cache or entry['url'] in failed:

                        # or if it repeats that of a previous candidate in this run.
                        if entry['url'] in entry_urls:
                            log.verbose('Encountered a duplicate index URL. Rejecting this instance of %$.' % (entry['title']))
                            continue

                        # Attach its index page separately,
                        entry['parse_urls'] = [entry['url']]

                        # in case of an identically named candidate later.
                        if entry['title'] in entry_titles:
                            entry_title = entry['title']
                            entry_url = entry['url']

                            # If so, its index page to the first candidate
                            for entry in entries:
                                if entry['title'] == entry_title:
                                    entry['parse_urls'].append(entry_url)
                                    entry_urls.add(entry_url)
                                    log.verbose('Encountered another instance of %s. Folding it into the existing entry.' % entry_title)

                                    # and reject the identically named candidate.
                                    break
                                else: continue

                        # Keep the candidate
                        else:
                            entries.append(entry)

                            # Note its title and URL for comparison
                            entry_titles.add(entry['title'])
                            entry_urls.add(entry['url'])

                    # If the candidate is in the cache, note its URL for future runs
                    else:
                        entry_urls.add(entry['url'])

        # Save entry URLs for future runs, and complete execute_plugins
        log.debug('Saving entry URLs for future runs.')
        task.simple_persistence['parse_urls_cache'] = entry_urls
        return entries

    def execute_parsing(self, task, config, entries): # added 'task' to accommodate html.py's requirements
        """
        :param config: Parse_URLs plugin config
        :param entries: List of pseudo entries to parse
        :return: List of entries found by parsing
        """

        # For each entry
        for index, entry in enumerate(entries):
            log.verbose('Parsing `%s` (%i of %i)' %
                        (entry['title'], index + 1, len(entries)))

            # Create container for parsed URLs
            entry['parsed_urls'] = []

            # Parse each index page for URLs
            for url in entry['parse_urls']:
                page = task.requests.get(url) # This is where task is invoked
                log.debug('Response: %s (%s)' % (page.status_code, page.reason))
                soup = get_soup(page.content)

                # Filter each URL
                for link in soup.find_all('a'):
                    regexps = config.get('links_re', None)
                    if regexps:
                        accept = False
                        for regexp in regexps:
                            if re.search(regexp, link['href']):
                                accept = True
                                log.debug('ACCEPTED: %s' % (link['href']))
                        if not accept:
                            log.debug('REJECTED: %s' % (link['href']))
                            continue

                    # Add accepted URLs
                    entry['parsed_urls'].append(link['href'])

        return entries

    @cached('parsed_urls')
    def on_task_input(self, task, config):
        task.no_entries_ok = True
        entries = self.execute_inputs(config, task)
        if len(entries) == 0:
            log.verbose('No new titles to parse.')
        else:
            log.verbose('Parsing the URLs of %i titles ...' % len(entries))
        if len(entries) > 500:
            log.critical('Looks like your inputs in parse_urls configuration produced '
                         'over 500 entries, please reduce the amount!')
        return self.execute_parsing(task, config, entries) # ! added 'task' to accommodate html.py's requirements


@event('plugin.register')
def register_plugin():
    plugin.register(Parse_URLs, 'parse_urls', api_ver=2)
