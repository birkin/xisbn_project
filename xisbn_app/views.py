# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint
from . import settings_app
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from xisbn_app.lib import view_info_helper
from xisbn_app.lib.xisbn import XHelper


log = logging.getLogger(__name__)
xisbn_helper = XHelper()


def info( request ):
    """ Returns basic data including branch & commit. """
    # log.debug( 'request.__dict__, ```%s```' % pprint.pformat(request.__dict__) )
    rq_now = datetime.datetime.now()
    commit = view_info_helper.get_commit()
    branch = view_info_helper.get_branch()
    info_txt = commit.replace( 'commit', branch )
    resp_now = datetime.datetime.now()
    taken = resp_now - rq_now
    context_dct = view_info_helper.make_context( request, rq_now, info_txt, taken )
    output = json.dumps( context_dct, sort_keys=True, indent=2 )
    return HttpResponse( output, content_type='application/json; charset=utf-8' )


def alternates( request, isbn_value ):
    """ Returns list of unfiltered list of isbns. """
    if xisbn_helper.check_isbn_validity( isbn_value ) is not True:
        return HttpResponseBadRequest( 'invalid ISBN' )
    alternates = xisbn_helper.get_alternates()
    resp = xisbn_helper.make_response( alternates )
    return resp


# def alternates( request, isbn_value ):
#     return HttpResponse( 'alternates response coming for `%s`' % isbn_value )


def filtered_alternates( request, isbn_value ):
    return HttpResponse( 'filtered_alternates response coming for `%s`' % isbn_value )
