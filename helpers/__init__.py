# -*- encoding: utf-8 -*-

import os, random, string,importlib
from django.conf import settings

from helpers.common import *
from helpers.util   import *

def cfg_val( aVarName ): 

    return getattr(settings, aVarName, None)

def name_to_class(name: str):

    cls_name    = name.split('.')[-1]
    cls_import  = name.replace('.'+cls_name, '') 

    module = importlib.import_module(cls_import)
    return getattr(module, cls_name)

def get_session_key(request, key, default=None):
    if key in request.session:
        return request.session[ key ]
    else:
        return default

def get_active_model(request):
    
    # Pick the first key
    DEFAULT_MODEL = list(settings.DYNAMIC_DATATB.keys())[0] 
    
    r_model_name      = get_session_key(request, 'active_model', DEFAULT_MODEL)
    r_model_form_name = settings.DYNAMIC_DATATB[ r_model_name ] 

    r_model      = name_to_class( r_model_name ) 
    r_model_form = name_to_class( r_model_form_name ) 

    return r_model, r_model_form

def h_random(aLen=16):
    letters = string.ascii_letters
    digits  = string.digits
    chars   = '_<>,.+'
    return ''.join(random.choices( letters + digits + chars, k=aLen))

def h_random_ascii(aLen=16):
    letters = string.ascii_letters
    digits  = string.digits
    return ''.join(random.choices( letters + digits, k=aLen))

def get_client_ip(request):
    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[-1].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

        # Convert to INT
        return ip 

    except:
        return -1