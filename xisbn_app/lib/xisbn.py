# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint, time
import isbnlib
from django.core.cache import cache
from django.http import HttpResponse
from xisbn_app.models import XisbnTracker



log = logging.getLogger(__name__)


class XHelper( object ):
    """ Helper for v1 api route. """

    def __init__( self ):
        log.debug( 'initializing XHelper()' )
        # self.legit_services = [ 'isbn', 'oclc' ]
        self.canonical_isbn = ''
        self.cached_status = ''

    def check_isbn_validity( self, isbn ):
        """ Returns boolean.
            Called by views.alternates() and views.filtered_alternates() """
        validity = False
        try:
            self.canonical_isbn = isbnlib.get_canonical_isbn( isbn, output='isbn13' )  # will return None on bad isbn
            validity = isbnlib.is_isbn13( self.canonical_isbn )  # will raise exception on None
        except Exception as e:
            log.warning( 'exception assessing validity, ```%s```; looks like ```%s``` is not valid' % (e, isbn) )
        log.debug( 'validity, `%s`' % validity )
        return validity

    def get_alternates( self ):
        """ Returns list of alternates.
            Called by views.alternates() """
        alternates = []
        try:
            trckr = XisbnTracker.objects.get( canonical_isbn=self.canonical_isbn )
        except:
            log.debug( 'new xisb-tracker-record will be created' )
            trckr = XisbnTracker( canonical_isbn=self.canonical_isbn )
            trckr.save()
        if trckr.alternates:
            alternates = json.loads( trckr.alternates )
        log.debug( 'alternates, ```%s```' % alternates )
        return alternates

    def get_filtered_alternates( self, alternates ):
        """ Returns list of filtered alternates.
            Called by views.filtered_alternates() """
        filtered_alternates = []
        try:
            info_dct = isbnlib.meta(self.canonical_isbn, service='default', cache='default')
        except Exception as e:
            log.error( 'exception loading metadata, ```%s```; returning empty filtered_alternates list' % e )
            return []
        language_code = info_dct.get( 'Language', None )
        log.debug( 'language_code, `%s`' % language_code )
        if language_code is None:
            return []
        for possible_isbn in alternates:
            self.apply_filter( possible_isbn, language_code, filtered_alternates )
        log.debug( 'filtered_alternates, ```%s```' % filtered_alternates )
        return filtered_alternates

    def apply_filter( self, possible_isbn, language_code, filtered_alternates ):
        """ Checks possible_isbn.
            Called by get_filtered_alternates() """
        time.sleep( 1 )
        alt_info_dct = alt_language_code = None
        try:
            alt_info_dct = json.loads( isbnlib.meta(possible_isbn, service='default', cache='default') )
        except Exception as e:
            log.warning( 'problem load metadata for possible_isbn, `%s`; error, ```%s```; continuing' % (possible_isbn, e) )
        if alt_info_dct:
            alt_language_code = alt_info_dct.get( 'Language', None )
        if language_code == alt_language_code:
            filtered_alternates.append( possible_isbn )
        return

    def make_alternates_response( self, request, alternates, start_time ):
        """ Builds unfiltered response.
            Called by views.alternates() """
        cntxt = {
            'request': {
                'url': '%s://%s%s' % ( request.scheme,
                    request.META.get( 'HTTP_HOST', '127.0.0.1' ),  # HTTP_HOST doesn't exist for client-tests
                    request.META.get('REQUEST_URI', request.META['PATH_INFO'])
                    ),
                'timestamp': str( start_time )
            },
            'response': {
                'alternates': alternates,
                'canonical_isbn': self.canonical_isbn,
                'elapsed_time': str( datetime.datetime.now()-start_time )
            }
        }
        output = json.dumps( cntxt, sort_keys=True, indent=2 )
        return HttpResponse( output, content_type='application/json; charset=utf-8' )

    def make_filtered_alternates_response( self, request, filtered_alternates, start_time ):
        """ Builds unfiltered response.
            Called by views.alternates() """
        cntxt = {
            'request': {
                'url': '%s://%s%s' % ( request.scheme,
                    request.META.get( 'HTTP_HOST', '127.0.0.1' ),  # HTTP_HOST doesn't exist for client-tests
                    request.META.get('REQUEST_URI', request.META['PATH_INFO'])
                    ),
                'timestamp': str( start_time )
            },
            'response': {
                'filtered_alternates': filtered_alternates,
                'canonical_isbn': self.canonical_isbn,
                'cached_status': self.cached_status,
                'elapsed_time': str( datetime.datetime.now()-start_time )
            }
        }
        output = json.dumps( cntxt, sort_keys=True, indent=2 )
        return HttpResponse( output, content_type='application/json; charset=utf-8' )

    ## end class XHelper()


class Processor( object ):
    """ Manager for grabbing enhanced and filtered info. """

    def __init__( self ):
        log.debug( 'initializing Processor()' )
        pass

    def get_alternates( self ):
        """ Returns list of alternates.
            Called by ? """
        alternates = isbnlib.editions( self.canonical_isbn, service='merge' )
        alternates = self.run_remove( alternates )
        log.debug( 'alternates, ```%s```' % alternates )
        return alternates

    def run_remove( self, alternates ):
        """ Removes target isbn from alternates list.
            Called by get_alternates() """
        try:
            alternates.remove( self.canonical_isbn )
            log.debug( 'isbn removed' )
        except:
            log.debug( 'canonical_isbn was not in alternates list' )
        return alternates

    ## end class Processor()




# def get_alternates( self ):
#     """ Returns list of alternates.
#         Called by views.alternates() """
#     alternates = cache.get( self.canonical_isbn )
#     if alternates is None:
#         self.cached_status = 'alternates_not_from_cache'
#         alternates = isbnlib.editions( self.canonical_isbn, service='merge' )
#         alternates = self._run_remove( alternates )
#         cache.set( self.canonical_isbn, alternates, (60*60*24*365) )  # (key, value, time-in-seconds) -- time argument is optional; defaults to settings.py entry
#     else:
#         self.cached_status = 'alternates_from_cache'
#     log.debug( 'cached_status, `%s`' % self.cached_status )
#     log.debug( 'alternates, ```%s```' % alternates )
#     return alternates
