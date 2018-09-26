# -*- coding: utf-8 -*-

from .models import XisbnTracker
from django.contrib import admin


class XisbnTrackerAdmin( admin.ModelAdmin ):
    list_display = [
        'canonical_isbn',
        'alternates',
        'filtered_alternates',
        'brown_filtered_alternates',
        'bfa_last_changed_date',
        'processing_status',
        'dt_created',
        'dt_modified'
        ]
    ordering = [ 'canonical_isbn' ]
    readonly_fields = [ 'dt_created', 'dt_modified' ]
    save_on_top = True


admin.site.register( XisbnTracker, XisbnTrackerAdmin )
