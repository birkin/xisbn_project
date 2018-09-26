# -*- coding: utf-8 -*-

"""
For log analysis.
"""

import datetime, glob, json, logging, os, pprint, sys

## configure django environment
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
cwd = os.getcwd()  # this assumes the cron call has cd-ed into the project directory
if cwd not in sys.path:
    sys.path.append( cwd )
django.setup()

## continue normal imports
from xisbn_app.models import XisbnTracker
from xisbn_app.lib.xisbn import Processor


logging.basicConfig(
    filename=os.environ['XISBN__LOG_PATH'],
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s',
    datefmt='%d/%b/%Y %H:%M:%S',
    )
log = logging.getLogger(__name__)

x_tracker = XisbnTracker()
processor = Processor()

os.nice( 19 )


class Enhancer( object ):
    """ Stores alternate, filtered_alternate, and brown_filtered_alternate data to db. """

    def __init__( self ):
        pass

    def process_isbn( self ):
        """ Controller function; manages preparation and saving of data to db.
            Called by cron-job or, eventually perhaps, rq worker. """
        tracker_record = self.find_record_to_process()
        processor.prepare_alternates( tracker_record )
        processor.prepare_filtered_alternates( tracker_record )
        processor.prepare_brown_filtered_alternates( tracker_record )
        return

    def find_record_to_process( self ):
        """ Grabs tracker record.
            Called by process_isbn() """
        trckr = XisbnTracker.objects.order_by('bfa_last_changed_date')[0]
        log.debug( 'trckr.canonical_isbn, `%s`' % trckr.canonical_isbn )
        return trckr

    ## end Enhancer()


if __name__ == '__main__':
    log.debug( '\n---\nstarting offline enhancer work' )
    enhancer = Enhancer()
    enhancer.process_isbn()
