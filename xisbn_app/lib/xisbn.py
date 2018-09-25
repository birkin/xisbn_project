# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint
import isbnlib
from django.core.cache import cache
from django.http import HttpResponse
# from xisbn_app import settings_app


log = logging.getLogger(__name__)


class XHelper( object ):
    """ Helper for v1 api route. """

    def __init__( self ):
        log.debug( 'initializing helper' )
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
            Called by views.alternates() and views.filtered_alternates() """
        cache_key = self.canonical_isbn
        alternates = cache.get( cache_key )
        if alternates is None:
            self.cached_status = 'alternates_not_from_cache'
            alternates = isbnlib.editions( self.canonical_isbn, service='merge' )
            cache.set( cache_key, alternates, (60*60*24*365) )  # time-in-seconds is optional last argument; defaults to settings.py entry
        else:
            self.cached_status = 'alternates_from_cache'
        log.debug( 'cached_status, `%s`' % self.cached_status )
        log.debug( 'alternates, ```%s```' % alternates )
        return alternates


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
                'cached_status': self.cached_status,
                'elapsed_time': str( datetime.datetime.now()-start_time )
            }
        }
        output = json.dumps( cntxt, sort_keys=True, indent=2 )
        return HttpResponse( output, content_type='application/json; charset=utf-8' )
