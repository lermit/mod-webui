#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

### Will be populated by the UI with it's own value
app = None

import os
import time
import re
import sys
mydir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, mydir)
import json

from shinken.log import logger
from shinken.misc.filter  import only_related_to
from shinken.misc.sorter import hst_srv_sort

from filters import hst_properties, sst_properties, hp_properties, sp_properties, match_search, match_check_period
from filters import match_hst, match_sst, match_hp, match_sp, match_contact, match_root_problem, match_business_impact
from filters import match_hg

# Our page
def get_page():
    return get_view('problems')

# Our page
def get_all():
    return get_view('all')

#  ops: list of the ops possible for this parameter
#  desc: label used for display
#  listed: list on the type select
filter_properties = {
    'hst': {'ops':['='], 'desc':'Host Status Type', 'listed':False, 'obj':'int', 'f':match_hst},
    'hp': {'ops':['='], 'desc':'Host Properties', 'listed':False, 'obj':'int', 'f':match_hp},
    'sst': {'ops':['='], 'desc':'Service Status Type', 'listed':False, 'obj':'int', 'f':match_sst},
    'sp': {'ops':['='], 'desc':'Service Status Type', 'listed':False, 'obj':'int', 'f':match_sp},
    'search': {'ops':['~','=','!='], 'desc':'Search', 'f':match_search},
    'check period': {'ops':['=', '!='], 'desc':'Check Period', 'obj':'timeperiod', 'f':match_check_period},
    'contact': {'ops':['=', '!='], 'desc':'Contact', 'obj':'contact', 'f':match_contact},
    'current attempt': {'ops':['=', '!=', '>=', '<='], 'desc':'Current Attempt', 'obj':'int', 'f':None},
    'downtime duration': {'ops':['>=', '<='], 'desc':'Downtime Duration', 'obj':'int', 'f':None},
    'execution time': {'ops':['>=', '<='], 'desc':'Execution Time', 'obj':'int', 'f':None},
    'host': {'ops':['=', '!=', '~', '!~'], 'desc':'Host', 'obj':'host', 'f':None},
    'hostgroup': {'ops':['=', '!='], 'desc':'Hostgroup', 'obj':'hostgroup', 'f':match_hg},
    'last check': {'ops':['>=', '<='], 'desc':'Last Check', 'obj':'int', 'f':None},
    'notification period': {'ops':['=', '!='], 'desc':'Notification Period', 'obj':'timeperiod', 'f':None},
    'nb of services': {'ops':['=', '!=', '>=', '<='], 'desc':'Number of Services', 'obj':'int', 'f':None},
    'parent': {'ops':['=', '!=', '~', '!~'], 'desc':'Parent', 'obj':'host', 'f':None},
    'realm': {'ops':['=', '!='], 'desc':'Realm', 'obj':'realm', 'f':None},
    'service': {'ops':['=', '!=', '~', '!~'], 'desc':'Service', 'obj':'service', 'f':None},
    'servicegroup': {'ops':['=', '!='], 'desc':'Servicegroup', 'obj':'servicegroup', 'f':None},
    'tag': {'ops':['=', '!=', '~', '!~'], 'desc':'Tag', 'obj':'tag', 'f':None},
    'pct state change': {'ops':['>=', '<='], 'desc':r'% State Change', 'obj':'int', 'f':None},
    'is root problem': {'ops':['=', '!='], 'desc':'Root Problem', 'obj':'bool', 'f':match_root_problem},
    'business impact': {'ops':['>=', '<=', '>', '<', '=', '!='], 'desc':'Business Impact', 'obj':'int', 'f':match_business_impact},
    }


# For exporting into javascript, we remove all functions from this dict
clean_filter_properties = {}
for (k,v) in filter_properties.iteritems():
    d = {}
    clean_filter_properties[k] = d
    for (k2, v2) in v.iteritems():
        if not callable(v2):
            d[k2] = v2




def fill_up_nbsp(s, l):
    if len(s) >= l:
        return s
    s += '&nbsp;'* (l - len(s))
    return s



def analyse_arg(filters, k, v):
    print "GROK analysing",k ,v
    elts = k.split('-')
    if len(elts) != 4:
        print "INVALID ARG FOR FILTERING", k, v
        return None
    FN = elts[1]
    KN = elts[2]
    part = elts[3]
    if part not in ['type', 'op', 'value']:
        print "INVALID ARG FOR FILTERING", k, v
        return None
    print "GROK:", FN, KN, part
    f = get_F(filters, FN)
    print "GROK UPDATE", f
    k = get_K(f, KN)

    # Type setting is quite easy, it must be a valid filter_properties entry
    if part == 'type':
        if len(v) == 0:
            print "INVALID ARG FOR FILTERING", k, v
            return None
        t = v[0]
        print "GROK: trying to set type", t
        if not t in filter_properties:
            print "INVALID ARG FOR FILTERING", k, v
            return None
        k['type'] = t
        return
    
    # op can be void. If so, use the first possible entry
    if part == 'op':
        t = k['type']
        e = filter_properties[t]
        op = '='
        if len(v) > 0:
            op = v[0]
        
        # By default the op is at the first value of the entry
        if not op in e['ops']:
            op = e['ops'][0]
        k['op'] = op
        return


    # We lok at the obj entry of the properties, and try to objectify the value
    if part == 'value':
        t = k['type']
        e = filter_properties[t]
        val = ''
        if len(v) > 0:
            val = v[0]
        obj = e.get('obj', None)
        if not obj:
            k['value'] = val
            return
        if obj == 'int':
            k['value'] = int(val)
            return
        if obj == 'bool':
            if val.lower() in ['1', 'true', 'on']:
                k['value'] = True
            else:
                k['value'] = False
            return
        k['value'] = val
        return

            
            
    

def gef_default_F(F):
    return {'name':F, 'value': [
            {'kn':'K1', 'fn':F, 'type':'hst', 'op':'=', 'value': 15},
            {'kn':'K2', 'fn':F, 'type':'hp',  'op':'=', 'value': 0},
            {'kn':'K3', 'fn':F, 'type':'sst', 'op':'=', 'value': 31},
            {'kn':'K4', 'fn':F, 'type':'sp',  'op':'=', 'value': 0},
            ]}
    

# BIG OR statement, and inside a F: AND rule
def get_default_filters(FN):
    F = gef_default_F(FN)
    filters = [F]
    return filters


def get_F(filters, FN):
    for f in filters:
        if f['name'] == FN:
            return f
    # oups, still not there? ok create it
    f = gef_default_F(FN)
    filters.append(f)
    return f


def get_K(f, KN):
    fn = ''
    for k in f['value']:
        fn = k['fn']
        if k['kn'] == KN:
            return k
    # Still there? we give a simple new k that means 'all'
    k = {'kn':KN, 'fn':fn, 'type':'search',  'op':'~', 'value': ''}
    f['value'].append(k)
    return k


def do_filter_F(pack, f):
    res = set(pack)
    
    for k in f['value']:
        t = k['type']
        op = k['op']
        value = k['value']
        e = filter_properties.get(t, None)
        if not e:
            continue
        f = e.get('f', None)
        # If no filtering already coded, bypass it
        if not f:
            continue
        
        to_del = set()
        print 'GROK: APPLy FILTER',t, op, value, to_del
        for i in res:
            print "GROK: LOOK AT", i.get_name()
            r = f(app, i, op, value)
            if not r:
                to_del.add(i)
            #if t == 'search':
            #    name = i.get_full_name()
            #    if value not in name:
            #        print "GROK: IS TO BE DELETED", i.get_full_name()
            #        to_del.add(i)
        print "GROK: do_filter_F len to_del", len(to_del)
        # Now remove all bad item from the current result
        res = res.difference(to_del)
        print "GROK: do_filter_F len res afger difference", len(to_del)
    print "GROK: do_filter_F len result", len(res)
    return res
    

def do_filter(pack, filters):
    print "GROK: do_filter START len result", len(pack)
    res = set()
    tmp = []
    for f in filters:
        p = do_filter_F(pack, f)
        tmp.append(p)
    for p in tmp:
        res = res | p
    print "GROK: do_filter len result", len(res)
    return list(res)


quick_searches = [
    {'name':'hdown', 'path':'/all?inp-F1-K1-type=hst&sel-F1-K1-op=%3D&inp-F1-K1-value=6&inp-F1-K2-type=hp&sel-F1-K2-op=%3D&inp-F1-K2-value=67594&inp-F1-K3-type=sst&sel-F1-K3-op=%3D&inp-F1-K3-value=0&inp-F1-K4-type=sp&sel-F1-K4-op=%3D&inp-F1-K4-value=0',
     'display': 'Down Hosts',
     },
    
    {'name':'rootpbs', 'path':'/all?inp-F1-K1-type=hst&sel-F1-K1-op=%3D&inp-F1-K1-value=15&inp-F1-K2-type=hp&sel-F1-K2-op=%3D&inp-F1-K2-value=0&inp-F1-K3-type=sst&sel-F1-K3-op=%3D&inp-F1-K3-value=31&inp-F1-K4-type=sp&sel-F1-K4-op=%3D&inp-F1-K4-value=0&sel-F1-K5-type=is+root+problem&sel-F1-K5-op=%3D&inp-F1-K5-value=1',
     'display': 'Root Problems'
     },
    ]


# Our View code. We will get different data from all and /problems
# but it's mainly filtering changes
def get_view(page):
    
    user = app.get_user_auth()
    if not user:
        app.bottle.redirect("/user/login")
        
    print 'DUMP COMMON GET', app.request.GET.__dict__
    
   # Look for the toolbar pref
    tool_pref = app.get_user_preference(user, 'toolbar')
    # If void, create an empty one
    if not tool_pref:
        app.set_user_preference(user, 'toolbar', 'show')
        tool_pref = 'show'
    toolbar = app.request.GET.get('toolbar', '')
    print "Toolbar", tool_pref, toolbar
    if toolbar != tool_pref and len(toolbar) > 0:
        print "Need to change user prefs for Toolbar", 
        app.set_user_preference(user, 'toolbar', toolbar)
    tool_pref = app.get_user_preference(user, 'toolbar')


    # We will keep a trace of our filters
    filtersold = {}
    ts = ['hst_srv', 'hg', 'realm', 'htag', 'ack', 'downtime', 'crit']
    for t in ts:
        filtersold[t] = []

    search = app.request.GET.get('global_search', '')

    # Most of the case, search will be a simple string, if so
    # make it a list of this string
    if isinstance(search, basestring):
        search = [search]


    
    quick_search = app.request.GET.get('quick-search', '')
    

    # Load the columns that this user want
    cols = app.get_user_preference(user, 'tab_cols')
    if not cols:
        app.set_user_preference(user, 'cols', '0')
        cols = '0'
    cols = int(json.loads(cols))

    tab_nb_elts =  app.get_user_preference(user, 'tab_nb_elts')
    if not tab_nb_elts:
        app.set_user_preference(user, 'tab_nb_elts', '30')
        tab_nb_elts = '30'
    tab_nb_elts = int(json.loads(tab_nb_elts))

    # Load the bookmarks
    bookmarks_r = app.get_user_preference(user, 'bookmarks')
    if not bookmarks_r:
        app.set_user_preference(user, 'bookmarks', '[]')
        bookmarks_r = '[]'
    bookmarks = json.loads(bookmarks_r)
    bookmarks_ro = app.get_common_preference('bookmarks')
    if not bookmarks_ro:
        bookmarks_ro = '[]'

    bookmarksro = json.loads(bookmarks_ro)
    bookmarks = json.loads(bookmarks_r)


    # We want to limit the number of elements
    start = int(app.request.GET.get('start', '0'))
    end = int(app.request.GET.get('end', '%d'%tab_nb_elts))


    items = []
    if page == 'problems':
        items = app.datamgr.get_all_problems(to_sort=False, get_acknowledged=True)
    elif page == 'all':
        items = app.datamgr.get_all_hosts_and_services()
    else:  # WTF?!?
        app.bottle.redirect("/problems")

    # Filter with the user interests
    items = only_related_to(items, user)

    # Filter by name if need by global_search
    for s in search:
        # We compile the pattern
        pat = re.compile(s, re.IGNORECASE)
        new_items = []
        for i in items:
            if pat.search(i.get_full_name()):
                new_items.append(i)
                continue
            to_add = False
            for imp in i.impacts:
                if pat.search(imp.get_full_name()):
                    to_add = True
            for src in i.source_problems:
                if pat.search(src.get_full_name()):
                    to_add = True
            if to_add:
                new_items.append(i)
        
        items = new_items
    

    # Now parse the GET input to find some filters :)
    filters = get_default_filters('F1')

    args = {}
    for (_, args) in app.request.GET.__dict__.iteritems():
        pass
    logger.debug("GROK1 %s" % args)
    for (k,v) in args.iteritems():
        logger.debug("GROK:"+ str(k)+ str(type(k))+ str(v)+ str(type(v)))
        if k.startswith('inp-') or k.startswith('sel-'):
            analyse_arg(filters, k, v)


    logger.debug("GROK FILTERS %s" % filters)

    items = do_filter(items, filters)

    """
    # Ok, if need, appli the search filter
    for s in search:
        s = s.strip()
        if not s:
            continue

        print "SEARCHING FOR", s
        print "Before filtering", len(items)

        elts = s.split(':', 1)
        t = 'hst_srv'
        if len(elts) > 1:
            t = elts[0]
            s = elts[1]

        print 'Search for type %s and pattern %s' % (t, s)
        if not t in filters:
            filters[t] = []
        filters[t].append(s)

        if t == 'hst_srv':
            # We compile the pattern
            pat = re.compile(s, re.IGNORECASE)
            new_items = []
            for i in items:
                if pat.search(i.get_full_name()):
                    new_items.append(i)
                    continue
                to_add = False
                for imp in i.impacts:
                    if pat.search(imp.get_full_name()):
                        to_add = True
                for src in i.source_problems:
                    if pat.search(src.get_full_name()):
                        to_add = True
                if to_add:
                    new_items.append(i)

            items = new_items

        if t == 'hg':
            hg = app.datamgr.get_hostgroup(s)
            print 'And a valid hg filtering for', s
            items = [i for i in items if hg in i.get_hostgroups()]

        if t == 'realm':
            r = app.datamgr.get_realm(s)
            print 'Add a realm filter', r
            items = [i for i in items if i.get_realm() == r]

        if t == 'htag':
            print 'Add a htag filter', s
            items = [i for i in items if s in i.get_host_tags()]

        if t == 'ack':
            print "Got an ack filter", s
            if s == 'false':
                # First look for hosts, so ok for services, but remove problem_has_been_acknowledged elements
                items = [i for i in items if i.__class__.my_type == 'service' or not i.problem_has_been_acknowledged]
                # Now ok for hosts, but look for services, and service hosts
                items = [i for i in items if i.__class__.my_type == 'host' or (not i.problem_has_been_acknowledged and not i.host.problem_has_been_acknowledged)]
            if s == 'true':
                # First look for hosts, so ok for services, but remove problem_has_been_acknowledged elements
                items = [i for i in items if i.__class__.my_type == 'service' or i.problem_has_been_acknowledged]
                # Now ok for hosts, but look for services, and service hosts
                items = [i for i in items if i.__class__.my_type == 'host' or (i.problem_has_been_acknowledged or i.host.problem_has_been_acknowledged)]

        if t == 'downtime':
            print "Got an downtime filter", s
            if s == 'false':
                # First look for hosts, so ok for services, but remove problem_has_been_acknowledged elements
                items = [i for i in items if i.__class__.my_type == 'service' or not i.in_scheduled_downtime]
                # Now ok for hosts, but look for services, and service hosts
                items = [i for i in items if i.__class__.my_type == 'host' or (not i.in_scheduled_downtime and not i.host.in_scheduled_downtime)]
            if s == 'true':
                # First look for hosts, so ok for services, but remove problem_has_been_acknowledged elements
                items = [i for i in items if i.__class__.my_type == 'service' or i.in_scheduled_downtime]
                # Now ok for hosts, but look for services, and service hosts
                items = [i for i in items if i.__class__.my_type == 'host' or (i.in_scheduled_downtime or i.host.in_scheduled_downtime)]

        if t == 'crit':
            print "Add a criticity filter", s
            items = [i for i in items if (i.__class__.my_type == 'service' and i.state_id == 2) or (i.__class__.my_type == 'host' and i.state_id == 1)]



        print "After filtering for", t, s, 'we got', len(items)
    
    # If we are in the /problems and we do not have an ack filter
    # we apply by default the ack:false one
    print "Late problem filtering?", page == 'problems', len(filters['ack']) == 0
    if page == 'problems' and len(filters['ack']) == 0:
        # First look for hosts, so ok for services, but remove problem_has_been_acknowledged elements
        items = [i for i in items if i.__class__.my_type == 'service' or not i.problem_has_been_acknowledged]
        # Now ok for hosts, but look for services, and service hosts
        items = [i for i in items if i.__class__.my_type == 'host' or (not i.problem_has_been_acknowledged and not i.host.problem_has_been_acknowledged)]

    # If we are in the /problems and we do not have an ack filter
    # we apply by default the ack:false one
    print "Late problem filtering?", page == 'problems', len(filters['downtime']) == 0
    if page == 'problems' and len(filters['downtime']) == 0:
        # First look for hosts, so ok for services, but remove problem_has_been_acknowledged elements
        items = [i for i in items if i.__class__.my_type == 'service' or not i.in_scheduled_downtime]
        # Now ok for hosts, but look for services, and service hosts
        items = [i for i in items if i.__class__.my_type == 'host' or (not i.in_scheduled_downtime and not i.host.in_scheduled_downtime)]
    
    """

    # Now sort it!
    items.sort(hst_srv_sort)

    total = len(items)
    # If we overflow, came back as normal
    if start > total:
        start = 0
        end = tab_nb_elts
    
    navi = app.helper.get_navi(total, start, step=tab_nb_elts)
    items = items[start:end]
    
    return {'app': app, 'pbs': items, 'user': user, 'navi': navi, 'search': '&'.join(search), 'page': page, 'filters': filtersold, 'bookmarks': bookmarks, 'bookmarksro': bookmarksro, 'toolbar': tool_pref, 'filters2':filters, 'hst_properties':hst_properties, 'hp_properties':hp_properties, 'sst_properties':sst_properties, 'sp_properties':sp_properties, 'filter_properties':clean_filter_properties, 'cols':cols, 'tab_nb_elts':tab_nb_elts, 'quick_searches':quick_searches}



default_options = [ {'name': 'search', 'value': '', 'type': 'text', 'label': 'Filter by name'},
                    {'name' : 'nb_elements', 'value': 10, 'type': 'int', 'label': 'Max number of elements to show'},
                   ]



# Our page
def get_pbs_widget():

    user = app.get_user_auth()
    if not user:
        app.bottle.redirect("/user/login")

    # We want to limit the number of elements, The user will be able to increase it
    nb_elements = max(0, int(app.request.GET.get('nb_elements', '10')))
    search = app.request.GET.get('search', '')

    pbs = app.datamgr.get_all_problems(to_sort=False)

    # Filter with the user interests
    pbs = only_related_to(pbs, user)

    # Sort it now
    pbs.sort(hst_srv_sort)

    # Ok, if need, appli the search filter
    if search:
        print "SEARCHING FOR", search
        print "Before filtering", len(pbs)
        # We compile the pattern
        pat = re.compile(search, re.IGNORECASE)
        new_pbs = []
        for p in pbs:
            if pat.search(p.get_full_name()):
                new_pbs.append(p)
                continue
            to_add = False
            for imp in p.impacts:
                if pat.search(imp.get_full_name()):
                    to_add = True
            for src in p.source_problems:
                if pat.search(src.get_full_name()):
                    to_add = True
            if to_add:
                new_pbs.append(p)

        pbs = new_pbs[:nb_elements]
        print "After filtering", len(pbs)

    pbs = pbs[:nb_elements]

    wid = app.request.GET.get('wid', 'widget_problems_' + str(int(time.time())))
    collapsed = (app.request.GET.get('collapsed', 'False') == 'True')

    options = {'search': {'value': search, 'type': 'text', 'label': 'Filter by name'},
               'nb_elements': {'value': nb_elements, 'type': 'int', 'label': 'Max number of elements to show'},
               }

    title = 'IT problems'
    if search:
        title = 'IT problems (%s)' % search

    return {'app': app, 'pbs': pbs, 'user': user, 'search': search, 'page': 'problems',
            'wid': wid, 'collapsed': collapsed, 'options': options, 'base_url': '/widget/problems', 'title': title,
            }





############### LARGE VERSION

default_large_options = [ {'name': 'global_search', 'value': '', 'type': 'text', 'label': 'Filter by name'},
                          {'name' : 'nb_elements', 'value': 10, 'type': 'int', 'label': 'Max number of elements to show'},
                          ]

def get_large_pbs_widget():

    user = app.get_user_auth()
    if not user:
        app.bottle.redirect("/user/login")
    
    d = get_view('problems')
    d['wid'] = app.request.GET.get('wid', 'widget_largeproblems_' + str(int(time.time())))
    d['collapsed'] = (app.request.GET.get('collapsed', 'False') == 'True')

    search = app.request.GET.get('global_search', '')
    nb_elements = app.request.GET.get('nb_elements', 10)
    d['options'] = {'global_search': {'value': search, 'type': 'text', 'label': 'Filter by name'},
                    'nb_elements': {'value': nb_elements, 'type': 'int', 'label': 'Max number of elements to show'},
                    }
    d['base_url'] = '/widget/largeproblems'
    d['title ']= 'IT problems'
    if search:
        d['title '] = 'IT problems (%s)' % search
        
    return d




default_last_options = [{'name': 'nb_elements', 'value': 10, 'type': 'int', 'label': 'Max number of elements to show'} ]


# Our page
def get_last_errors_widget():

    user = app.get_user_auth()
    if not user:
        app.bottle.redirect("/user/login")

    # We want to limit the number of elements, The user will be able to increase it
    nb_elements = max(0, int(app.request.GET.get('nb_elements', '10')))

    pbs = app.datamgr.get_problems_time_sorted()

    # Filter with the user interests
    pbs = only_related_to(pbs, user)

    # Keep only nb_elements
    pbs = pbs[:nb_elements]

    wid = app.request.GET.get('wid', 'widget_last_problems_' + str(int(time.time())))
    collapsed = (app.request.GET.get('collapsed', 'False') == 'True')

    options = {'nb_elements': {'value': nb_elements, 'type': 'int', 'label': 'Max number of elements to show'},
               }

    title = 'Last IT problems'

    return {'app': app, 'pbs': pbs, 'user': user, 'page': 'problems', 'fill_up_nbsp':fill_up_nbsp,
            'wid': wid, 'collapsed': collapsed, 'options': options, 'base_url': '/widget/last_problems', 'title': title,
            }

widget_display_name = 'IT problems'
widget_desc = '''Show the most impacting IT problems
'''

last_widget_display_name = 'Last IT problems'
last_widget_desc = '''Show the IT problems sorted by time
'''



pages = {get_page: {'routes': ['/problems'], 'view': 'problems', 'static': True},
         get_all: {'routes': ['/all'], 'view': 'problems', 'static': True},
         get_pbs_widget: {'routes': ['/widget/problems'], 'view': 'widget_problems', 'static': True, 'widget': ['dashboard'], 'widget_display_name':widget_display_name, 'widget_desc': widget_desc, 'widget_name': 'problems', 'widget_picture': '/static/tabular/img/widget_problems.png', 'widget_size': {'width':4, 'height':6}, 'widget_options':default_options , 'widget_favoritable':True},
         get_large_pbs_widget : {'routes': ['/widget/largeproblems'], 'view': 'widget_largeproblems', 'static': True, 'widget': ['dashboard'], 'widget_display_name':widget_display_name, 'widget_desc': 'IT problems (large)', 'widget_name': 'problems', 'widget_picture': '/static/tabular/img/widget_problems.png', 'widget_size': {'width':16, 'height':10}, 'widget_options':default_large_options, 'widget_favoritable':True },
         get_last_errors_widget: {'routes': ['/widget/last_problems'], 'view': 'widget_last_problems', 'static': True, 'widget': ['dashboard'], 'widget_display_name':last_widget_display_name, 'widget_desc': last_widget_desc, 'widget_name': 'last_problems', 'widget_picture': '/static/tabular/img/widget_problems.png', 'widget_size': {'width':4, 'height':6}, 'widget_options':default_last_options, 'widget_favoritable':True},
         }
