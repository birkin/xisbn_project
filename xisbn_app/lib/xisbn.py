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

    def prepare_alternates( self, x_record ):
        """ Prepares and saves list of alternates.
            Called by Enhancer.process_isbn() """
        alternates = isbnlib.editions( x_record.canonical_isbn, service='merge' )
        alternates = self.run_remove( alternates )
        now = datetime.datetime.now()
        data_dct = { 'prepared': str(now), 'alternates': alternates }
        x_record.alternates = json.dumps( data_dct )
        x_record.bfa_last_changed_date = datetime.datetime.now()
        x_record.save()
        log.debug( 'alternates, ```%s```' % x_record.alternates )
        return

    def run_remove( self, alternates ):
        """ Removes target isbn from alternates list.
            Called by get_alternates() """
        try:
            alternates.remove( self.canonical_isbn )
            log.debug( 'isbn removed' )
        except:
            log.debug( 'canonical_isbn was not in alternates list' )
        return alternates

    def prepare_filtered_alternates( self, x_record ):
        """ Prepares and saves list of filtered_alternates.
            Called by Enhancer.process_isbn() """
        canonical_language_code = self.get_isbn_meta( x_record )
        if not canonical_language_code:
            data_dct = { 'prepared': str(datetime.datetime.now()), 'filtered_alternates': [] }
        else:
            data_dct = self.loop_through_alternates( x_record )
        x_record.filtered_alternates = json.dumps( data_dct, sort_keys=True )
        # x_record.bfa_last_changed_date = datetime.datetime.now()
        x_record.save()
        log.debug( 'filtered_alternates, ```%s```' % x_record.filtered_alternates )
        return

    def get_isbn_meta( self, x_record ):
        """ Returns meta for language comparison.
            Called by prepare_filtered_alternates() """
        try:
            data_dct = isbnlib.meta(x_record.canonical_isbn, service='default', cache='default')
        except Exception as e:
            log.error( 'exception loading metadata, ```%s```' % e )
            return None
        x_record.canonical_meta = json.dumps( data_dct, sort_keys=True )
        # x_record.bfa_last_changed_date = datetime.datetime.now()
        x_record.save()
        language_code = data_dct.get( 'Language', None )
        log.debug( 'canonical-language_code, `%s`' % language_code )
        return language_code

    def loop_through_alternates( self, x_record ):
        """ Loops through each alternate, filtering on language code.
            Called by prepare_filtered_alternates() """
        filtered_alternates = []
        for alt_isbn in json.loads(x_record.alternates)['alternates'] :
            self.check_alt_isbn( alt_isbn, x_record, filtered_alternates )
            time.sleep( 10 )
        data_dct = { 'prepared': str(datetime.datetime.now()), 'filtered_alternates': filtered_alternates }
        return data_dct

    def check_alt_isbn( self, alt_isbn, x_record, filtered_alternates ):
        """ Checks alt_isbn language-code and adds it to filtered_isbns if it matches.
            Called by loop_through_alternates() """
        canonical_language_code = json.loads(x_record.canonical_meta)['Language']
        try:
            data_dct = isbnlib.meta( alt_isbn, service='default', cache='default' )
        except Exception as e:
            data_dct = {}
            log.warning( 'exception loading metadata, ```%s```; isbn was `%s`' % (e, alt_isbn) )
        alt_language_code = data_dct.get( 'Language', None )
        if alt_language_code == canonical_language_code:
            log.debug( 'alt_data_dct, ```%s```' % data_dct )
            filtered_alternates.append( {alt_isbn: data_dct} )
        return

    def prepare_brown_filtered_alternates( self, x_record ):
        """ Determines which of the filtered_isbns brown holds.
            Called by Enhancer.process_isbn() """
        brown_filtered_alternates = []
        filtered_alternates = json.loads(x_record.filtered_alternates)['filtered_alternates']
        for ( isbn_key, meta_dct_val ) in filtered_alternates:
            url = 'https://library.brown.edu/availability_api/v1/isbn/%s/' % isbn_key
            r = requests.get( url )
            if r.status_code == 200:
                sierra_holdings = r.json()['response']['sierra']
                if sierra_holdings:
                    for holding in sierra_holdings:
                        brown_filtered_alternates.append( {holding['isbn']: {'bib': holding['bib'], 'year': holding.get('pubyear', None)}} )
                x_record.brown_filtered_alternates = json.dumps( brown_filtered_alternates, sort_keys=True )
        x_record.bfa_last_changed_date = datetime.datetime.now()
        x_record.save()
        log.debug( 'brown_filtered_alternates, ```%s```' % x_record.filtered_alternates )
        return



    ## end class Processor()



# def apply_filter( self, possible_isbn, language_code, filtered_alternates ):
#     """ Checks possible_isbn.
#         Called by get_filtered_alternates() """
#     time.sleep( 1 )
#     alt_info_dct = alt_language_code = None
#     try:
#         alt_info_dct = json.loads( isbnlib.meta(possible_isbn, service='default', cache='default') )
#     except Exception as e:
#         log.warning( 'problem load metadata for possible_isbn, `%s`; error, ```%s```; continuing' % (possible_isbn, e) )
#     if alt_info_dct:
#         alt_language_code = alt_info_dct.get( 'Language', None )
#     if language_code == alt_language_code:
#         filtered_alternates.append( possible_isbn )
#     return


# def get_filtered_alternates( self, alternates ):
#     """ Returns list of filtered alternates.
#         Called by views.filtered_alternates() """
#     filtered_alternates = []
#     try:
#         info_dct = isbnlib.meta(self.canonical_isbn, service='default', cache='default')
#     except Exception as e:
#         log.error( 'exception loading metadata, ```%s```; returning empty filtered_alternates list' % e )
#         return []
#     language_code = info_dct.get( 'Language', None )
#     log.debug( 'language_code, `%s`' % language_code )
#     if language_code is None:
#         return []
#     for possible_isbn in alternates:
#         self.apply_filter( possible_isbn, language_code, filtered_alternates )
#     log.debug( 'filtered_alternates, ```%s```' % filtered_alternates )
#     return filtered_alternates


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
