# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint
from django.conf import settings as project_settings
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponseRedirect


log = logging.getLogger(__name__)


class XisbnTracker( models.Model ):
    canonical_isbn = models.CharField( max_length=13, null=True, blank=True )
    canonical_isbn_count = models.IntegerField( null=True, blank=True, default=0 )
    alternates = models.TextField( null=True, blank=True )
    filtered_alternates = models.TextField( null=True, blank=True )
    brown_filtered_alternates = models.TextField( null=True, blank=True )
    bfa_last_changed_date = models.DateTimeField()
    dt_created = models.DateTimeField( auto_now_add=True )
    dt_modified = models.DateTimeField( auto_now=True )
