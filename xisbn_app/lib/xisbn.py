# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint
import isbnlib
from django.core.cache import cache


log = logging.getLogger(__name__)


class XHelper( object ):
    """ Helper for v1 api route. """

    def __init__( self ):
        log.debug( 'initializing helper' )
        # self.legit_services = [ 'isbn', 'oclc' ]
        self.canonical_isbn = ''

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
            log.debug( 'alternates were not in cache' )
            alternates = isbnlib.editions( self.canonical_isbn, service='merge' )
            cache.set( cache_key, alternates )  # time-in-seconds could be last argument; defaults to settings.py entry
        else:
            log.debug( 'alternates were in cache' )
        log.debug( 'alternates, ```%s```' % pprint.pformat(alternates) )
        return alternates

