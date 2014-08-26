from shinken.log import logger


hst_properties = [
    {'desc':'Up'},
    {'desc':'Down'},
    {'desc':'Unreachable'},
    {'desc':'Pending'},
]


sst_properties = [
    {'desc':'Ok'},
    {'desc':'Warning'},
    {'desc':'Critical'},
    {'desc':'Unknown'},
    {'desc':'Pending'},
]


hp_properties_raw = [
    # Downtime
    {'desc': 'In Scheduled Downtime', 'f': lambda i: i.in_scheduled_downtime},   
    {'desc': 'Not In Scheduled Downtime', 'f': lambda i: not i.in_scheduled_downtime},
    # Acknowledged
    {'desc': 'Has Been Acknowledged', 'f': lambda i: i.problem_has_been_acknowledged },
    {'desc': 'Has Not Been Acknowledged', 'f': lambda i: not i.problem_has_been_acknowledged},
    # Check enabled/disabled
    {'desc': 'Checks Disabled', 'f': lambda i: not i.active_checks_enabled},
    {'desc': 'Checks Enabled', 'f': lambda i: i.active_checks_enabled},
    # Event Handlers
    {'desc': 'Event Handler Disabled', 'f': lambda i: not i.event_handler_enabled},
    {'desc': 'Event Handler Enabled', 'f': lambda i: i.event_handler_enabled},
    # Flapping
    {'desc': 'Flap Detection Disabled', 'f': lambda i: not i.flap_detection_enabled},
    {'desc': 'Flap Detection Enabled', 'f': lambda i: i.flap_detection_enabled},
    {'desc': 'Is Flapping', 'f': lambda i: i.is_flapping},     
    {'desc': 'Is Not Flapping', 'f': lambda i: not i.is_flapping},
    # Notifications
    {'desc': 'Notifications Disabled', 'f': lambda i: not i.notifications_enabled},
    {'desc': 'Notifications Enabled', 'f': lambda i: i.notifications_enabled},
    # Passive checks
    {'desc': 'Passive Checks Disabled', 'f': lambda i: not i.passive_checks_enabled}, 
    {'desc': 'Passive Checks Enabled', 'f': lambda i: i.passive_checks_enabled},
    #WTF??{'desc': 'Passive Checks'},          {'desc': 'Active Checks'},
    # HARD/SOFT
    {'desc': 'In Hard State', 'f': lambda i: i.state_type == 'HARD'},
    {'desc': 'In Soft State', 'f': lambda i: i.state_type == 'SOFT'},
    # NOT TRIVIAL
    {'desc': 'In Check Period'},         {'desc': 'Outside Check Period'},
    {'desc': 'In Notification Period'},  {'desc': 'Outside Notification Period'},
    {'desc': 'Has Modified Attributes'}, {'desc': 'No Modified Attributes'},
]


# Services are alike hosts in fact
sp_properties_raw = hp_properties_raw

hp_properties = []
for v in hp_properties_raw:
    d = {}
    hp_properties.append(d)
    for (k2, v2) in v.iteritems():
        if not callable(v2):
            d[k2] = v2

sp_properties = hp_properties

# Match host by looking at their state
def match_hst(app, i, op, value):
    # A service is not interesting, look at its host instead
    if i.__class__.my_type == 'service':
        i = i.host
    # Ok real host now
    state = i.state
    idx = 0
    j = 0
    for d in hst_properties:
        if d['desc'].upper() == state:
            idx = j
        j += 1

    mask = 1 << idx   # Look for the idx bit
    m = value & mask
    if m != 0:
        return True
    else:
        return False



# Match services by looking at their state
def match_sst(app, i, op, value):
    # An host is always OK there
    if i.__class__.my_type == 'host':
        return True
    # Ok real host now
    state = i.state
    idx = 0
    j = 0
    for d in sst_properties:
        if d['desc'].upper() == state:
            idx = j
        j += 1

    mask = 1 << idx   # Look for the idx bit
    m = value & mask
    if m != 0:
        return True
    else:
        return False



# Match host by looking at their state
def match_hp(app, i, op, value):
    # A service is not interesting, look at its host instead
    if i.__class__.my_type == 'service':
        return True
    
    j = -1
    for d in hp_properties_raw:
        j += 1
        mask = 1 << j #
        m = value & mask
        # If we do not look for this entry, by pass it
        if m == 0:
            continue
        f = d.get('f', None)
        if not f:
            continue
        b = f(i)
        return b
    return True


# Match host by looking at their state
def match_sp(app, i, op, value):
    # A service is not interesting, look at its host instead
    if i.__class__.my_type == 'host':
        return True
    
    j = -1
    for d in sp_properties_raw:
        j += 1
        mask = 1 << j #
        m = value & mask
        # If we do not look for this entry, by pass it
        if m == 0:
            continue
        f = d.get('f', None)
        if not f:
            continue
        b = f(i)
        return b
    return True


# Search by the full name
# TODO: manage op
def match_search(app, i, op, value):
    name = i.get_full_name()
    return value in name


# Search by the full name
def match_hg(app, i, op, value):
    o = i
    if i.__class__.my_type == 'service':
        o = i.host
    if op == '=':
        for hg in o.hostgroups:
            if hg.get_name().startswith(value):
                return True
        # By default if search only for, negative is False
        return False
    if op == '!=':
        for hg in o.hostgroups:
            if hg.get_name().startswith(value):
                return False
        # If search for ALL but, means if not, True
        return True


# TODO: manage op better
def match_check_period(app, i, op, value):
    tp = i.check_period

    # If we got no timeperiod, the only Tue result
    # is when the value is void
    if not tp:
        return not value

    tpname = tp.get_name()
    return value == tpname
    

def match_contact(app, i, op, value):
    contacts = i.contacts
    
    for c in contacts:
        cname = c.get_name()
        if value in cname:
            return True
    return False




# Search by the full name
# TODO: manage op
def match_root_problem(app, i, op, value):
    #logger.log('ASKING'+i.get_full_name()+' if '+str(i.is_problem)+' '+op+' '+str(value)+' '+str(type(value)))
    if op == '=':
        return i.is_problem == value
    else:
        return i.is_problem != value    


# Search by the full name
# TODO: manage op
def match_business_impact(app, i, op, value):
    if op == '<=':
        return i.business_impact <= value
    if op == '<':
        return i.business_impact < value
    if op == '>=':
        return i.business_impact >= value
    if op == '>':
        return i.business_impact > value
    if op == '==':
        return i.business_impact == value
    if op == '!=':
        return i.business_impact != value
    return True
