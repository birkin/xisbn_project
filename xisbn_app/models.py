# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint
from django.conf import settings as project_settings
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponseRedirect


log = logging.getLogger(__name__)


class XisbnTracker( models.Model ):
    canonical_isbn = models.CharField( max_length=13, null=True, blank=True )
    canonical_isbn_count = models.IntegerField( default=0, null=True, blank=True )
    alternates = models.TextField( null=True, blank=True )
    filtered_alternates = models.TextField( null=True, blank=True )
    brown_filtered_alternates = models.TextField( null=True, blank=True )
    bfa_last_changed_date = models.DateTimeField( null=True, blank=True )
    processing_status = models.CharField( max_length=20, default='not_yet_processed', null=True, blank=True )  # or 'in_process' or 'processd'
    dt_created = models.DateTimeField( auto_now_add=True )
    dt_modified = models.DateTimeField( auto_now=True )
