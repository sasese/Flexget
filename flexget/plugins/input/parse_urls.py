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

    DEFAULT_ALL_ENTRIES = False

    schema = {
        'oneOf': [
            {'type': 'object',
                'properties': {
                    'inputs': {'type': 'array', 'items': {
                        'allOf': [{'$ref': '/schema/plugins?phase=input'}, {'maxProperties': 1, 'minProperties': 1}]
                    }},
                    'links_re': one_or_more({'type': 'string'}),
                    'all_entries': {'type': 'boolean'},                },
                'additionalProperties': False
             }
        ]
    }

    def execute_inputs(self, config, task):
        """
        :param config: Parse_URLs config
        :param task: Current task
        :return: List of pseudo entries created by inputs under `inputs` configuration
        """

        cache = []
        if not config.get('all_entries', self.DEFAULT_ALL_ENTRIES):
            for index, item in enumerate(config['inputs']):
                cache += task.simple_persistence.get('parse_urls_cache_%s' % index, [])

        entries = []
        entry_titles = list ()
        entry_urls = list ()

        # Get candidate entries from plugins
        for index, item in enumerate(config['inputs']):

            for input_name, input_config in item.iteritems():

                entry_titles_reference_point = list(entry_titles)

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

                # Each candidate,
                for entry in candidate_entries:

                    # whose title does not repeat that in a previous run,
                    if entry['title'] not in cache:

                        # nor the index page of a candidate accepted as entry in this run,
                        if entry['url'] not in entry_urls:

                            # or its title, is accepted as an entry.
                            if entry['title'] not in entry_titles:
                                entry['parse_urls'] = [entry['url']]
                                entries.append(entry)
                                log.debug('ACCEPTED: %s' % (entry['title']))

                                # Note its title and URL for comparison
                                entry_titles.append(entry['title'])
                                entry_urls.append(entry['url'])

                            # Should a candidate's title repeat that of an entry,
                            else:
                                entry_title = entry['title']
                                entry_url = entry['url']

                                # look up the entry,
                                for entry in entries:
                                    if entry['title'] == entry_title:

                                        # attach to it the index page of the candidate
                                        entry['parse_urls'].append(entry_url)
                                        entry_urls.append(entry_url)
                                        log.verbose('Duplicate title. Folding it into existing entry and rejecting this instance of %s.' % entry_title)

                                        # and reject the supernumerary
                                        break
                                    else: continue

                        else:
                            log.verbose('Duplicate index page. Rejecting this instance of %s.' % (entry['title']))
                            continue

                    # If the candidate is in the cache, maintain its title for future runs
                    else:
                        log.trace('Recently parsed title. Rejecting %s' % (entry['title']))
                        entry_titles.append(entry['title'])

                # Save plugin cache for future runs
                log.debug('Saving %s (%s) cache for future runs.' % (input_name, index))
                task.simple_persistence['parse_urls_cache_%s' % index] = list(set(entry_titles_reference_point) ^ set(entry_titles))

        # Complete execute_inputs
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

            # Create, or empty, the container for parsed URLs
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

    def execute_reparsing(self, task, entries):
        """Reparse backlog entries"""

        basic_entries = []
        parse_entries = []

        for entry in entries:
            if entry ['parse_urls']:
                parse_entries.append (entry)
            else:
                basic_entries.append (entry)

        parse_entries = self.execute_parsing(task, task.config.get('parse_urls', {}), entries)
        entries = parse_entries + basic_entries

        return entries

    @cached('parsed_urls')
    def on_task_input(self, task, config):
        task.no_entries_ok = True
        entries = self.execute_inputs(config, task)
        if len(entries) == 0:
            log.info('No new titles to parse.')
        else:
            log.info('Parsing %i titles ...' % len(entries))
        if len(entries) > 500:
            log.critical('Looks like your inputs in parse_urls configuration produced '
                         'over 500 entries, please reduce the amount!')
        return self.execute_parsing(task, config, entries) # ! added 'task' to accommodate html.py's requirements


@event('plugin.register')
def register_plugin():
    plugin.register(Parse_URLs, 'parse_urls', api_ver=2)
