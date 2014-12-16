from __future__ import unicode_literals, division, absolute_import
import datetime
import logging
import random
import re
import urlparse

from sqlalchemy import Column, Integer, DateTime, Unicode, Index

from flexget import options, plugin, validator
from flexget.event import event
from flexget.plugin import get_plugin_by_name, PluginError, PluginWarning
from flexget import db_schema
from flexget.config_schema import one_or_more
from flexget.utils.tools import parse_timedelta, multiply_timedelta
from flexget.utils.soup import get_soup

log = logging.getLogger('parse_urls')
Base = db_schema.versioned_base('parse_urls', 0)


'''
Notes

General:
This plugin is an assemblage of the discover and html input plugins, parsing candidate entries
provided by input plugins for URLs, filtering those if specified, and creating unified entries
per title attaching the parsed URLs.

To do:
Major: Work out ways to avoid flooding sites with parse requests and speed performance. Step one
       will be reliable caching of parsed entries for re-use across tasks, and tracking task results
       on those entries, to avoid parsing any item more than needed.
       
Considerations:
Major: All other plugins will be unaware of the new values ('parse_urls' and 'parsed_urls').
       Even if existing values were recycled (such as 'url' and 'urls') their altered nature
       would remain unused, without recoding of plugins.
'''


class Parse_URLsEntry(Base):
    __tablename__ = 'parse_urls_entry'

    id = Column(Integer, primary_key=True)
    title = Column(Unicode, index=True)
    task = Column(Unicode, index=True)
    last_execution = Column(DateTime)

    def __init__(self, title, task):
        self.title = title
        self.task = task
        self.last_execution = None

    def __str__(self):
        return '<Parse_URLsEntry(title=%s,task=%s,added=%s)>' % (self.title, self.task, self.last_execution)

Index('ix_parse_urls_entry_title_task', Parse_URLsEntry.title, Parse_URLsEntry.task)


@event('manager.db_cleanup')
def db_cleanup(session):
    value = datetime.datetime.now() - parse_timedelta('7 days')
    for de in session.query(Parse_URLsEntry).filter(Parse_URLsEntry.last_execution <= value).all():
        log.debug('deleting %s' % de)
        session.delete(de)


class Parse_URLs( object):
    """
    Parse URLs based on other inputs material.

    Example::

      parse_urls:
        inputs:
          - rss:
              url: http://example.com/feed
              group_links: yes
        links_re:
          - example\.com
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
                    result = method(task, input_config)
                except PluginError as e:
                    log.warning('Error during input plugin %s: %s' % (input_name, e))
                    continue
                if not result:
                    log.warning('Input %s did not return anything' % input_name)
                    continue

                # For each candidate
                for entry in result:
                    
                    # Reject if its index page repeats that of a previous candidate
                    if entry['url'] in entry_urls:
                        log.verbose('Encountered a duplicate index URL. Rejecting this instance of %$.' % (entry['title']))
                        continue

                    # Attach its index page separately
                    entry['parse_urls'] = [entry['url']]
                    
                    # In case of an identically named candidate later
                    if entry['title'] in entry_titles:
                        entry_title = entry['title']
                        entry_url = entry['url']
                        
                        # Attach its index page to the first candidate
                        for entry in entries:
                            if entry['title'] == entry_title:
                                entry['parse_urls'].append(entry_url)
                                log.verbose('Encountered another instance of %s. Folding it into the existing entry.' % entry_title)
                                
                                # And reject the identically named candidate
                                break
                            else: continue

                    # Keep the candidate
                    else:
                        entries.append(entry)
                        
                        # Note its title and URL for comparison
                        entry_titles.add(entry['title'])
                        entry_urls.add(entry['url'])
                        
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
                                log.debug('Accepted %s' % (link['href']))
                        if not accept:
                            log.debug('Rejected %s' % (link['href']))
                            continue
                    
                    # Add accepted URLs
                    entry['parsed_urls'].append(link['href'])

        #return sorted(result, reverse=True, key=lambda x: x.get('search_sort'))
        return entries

    def entry_complete(self, entry, query=None, parse_results=None, **kwargs):
        if entry.accepted:
            # One of the parse results was accepted, transfer the acceptance back to the query entry which generated it
            query.accept()
        # Remove this entry from the list of parse results yet to complete
        parse_results.remove(entry)
        # When all the parse results generated by a query entry are complete, complete the query which generated them
        if not parse_results:
            query.complete()

    def estimated(self, entries):
        """
        :return: Entries that we have estimated to be available
        """
        estimator = get_plugin_by_name('estimate_release').instance
        result = []
        for entry in entries:
            est_date = estimator.estimate(entry)
            if est_date is None:
                log.debug('No release date could be determined for %s' % entry['title'])
                result.append(entry)
                continue
            if type(est_date) == datetime.date:
                # If we just got a date, add a time so we can compare it to now()
                est_date = datetime.datetime.combine(est_date, datetime.time())
            if datetime.datetime.now() >= est_date:
                log.debug('%s has been released at %s' % (entry['title'], est_date))
                result.append(entry)
            else:
                entry.reject('has not been released')
                entry.complete()
                log.debug("%s hasn't been released yet (Expected: %s)" % (entry['title'], est_date))
        return result

    def interval_total_seconds(self, interval):
        """
        Because python 2.6 doesn't have total_seconds()
        """
        return interval.seconds + interval.days * 24 * 3600

    def interval_expired(self, config, task, entries):
        """
        Maintain some limit levels so that we don't hammer search
        sites with unreasonable amount of queries.

        :return: Entries that are up for ``config['interval']``
        """
        config.setdefault('interval', '5 hour')
        interval = parse_timedelta(config['interval'])
        if task.options.parse_urls_now:
            log.info('Ignoring interval because of --parse_urls-now')
        result = []
        interval_count = 0
        for entry in entries:
            de = task.session.query(Parse_URLsEntry).\
                filter(Parse_URLsEntry.title == entry['title']).\
                filter(Parse_URLsEntry.task == task.name).first()

            if not de:
                log.debug('%s -> No previous run recorded' % entry['title'])
                de = Parse_URLsEntry(entry['title'], task.name)
                task.session.add(de)
            if task.options.parse_urls_now or not de.last_execution:
                # First time we execute (and on --parse_urls-now) we randomize time to avoid clumping
                delta = multiply_timedelta(interval, random.random())
                de.last_execution = datetime.datetime.now() - delta
            else:
                next_time = de.last_execution + interval
                log.debug('last_time: %r, interval: %s, next_time: %r, ',
                          de.last_execution, config['interval'], next_time)
                if datetime.datetime.now() < next_time:
                    log.debug('interval not met')
                    interval_count += 1
                    entry.reject('parse_urls interval not met')
                    entry.complete()
                    continue
                de.last_execution = datetime.datetime.now()
            log.debug('interval passed')
            result.append(entry)
        if interval_count:
            log.verbose('Parse_URLs interval of %s not met for %s entries. Use --parse_urls-now to override.' %
                        (config['interval'], interval_count))
        return result

    def on_task_input(self, task, config):
        task.no_entries_ok = True
        entries = self.execute_inputs(config, task)
        log.verbose('Parsing the URLs of %i titles ...' % len(entries))
        if len(entries) > 500:
            log.critical('Looks like your inputs in parse_urls configuration produced '
                         'over 500 entries, please reduce the amount!')
        # TODO: the entries that are estimated should be given priority over expiration
        entries = self.interval_expired(config, task, entries)
        if not config.get('ignore_estimations', False):
            entries = self.estimated(entries)
        return self.execute_parsing(task, config, entries) # ! added 'task' to accommodate html.py's requirements


@event('plugin.register')
def register_plugin():
    plugin.register(Parse_URLs, 'parse_urls', api_ver=2)


@event('options.register')
def register_parser_arguments():
    options.get_parser('execute').add_argument('--parse_urls-now', action='store_true', dest='parse_urls_now',
                                               default=False, help='immediately try to parse_urls everything')
