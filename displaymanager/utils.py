#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db.models import Avg,Max,Min,Count
import re,sys,os
from datetime import *
from rapidsms.webui.utils import render_to_response, paginated
from locations.models import *
from reporters.models import *
from healthtables.models import *
from childhealth.models import *
from models import *
#auto gen this

def evalFunc(obj, attr):
    try:
        result = getattr(obj,attr.func)
        if (callable(result)):
            return result()
        else:
            return result
    except Exception,e:
       try:
            #return getattr(getattr(obj, attr.func.split(".")[0]),attr.func.split(".")[1])
            for i in attr.func.split("."): obj = getattr(obj,i) 
            try:
                if callable : return obj()
            except:
                pass
            return obj
       except Exception, e2:
            return obj 

    

def stringHash(value):
    pattern = "\%\((.*?)\)s.*"
    vals= re.findall(pattern,value)
    return dict(zip(vals,[]*len(vals)))
    return none

def dataEval(value,*args,**kwargs):
    try:
        if value.params == "" or value.params == "0": #remove 0 temp f#$k up
             cmd = "%s.objects.all()" % (value.klass)
        else:
             cmd = "%s.objects.filter(%s)" % (value.klass,value.params) % kwargs

        if value.filterorder: cmd = "%s.order_by(\"%s\")" % (cmd,value.filterorder)
        data = eval(cmd) 
        if args: return [dict(map(lambda a: (a,evalFunc(d,a)),args)) for d in data]
        return data
    except Exception,e:
        return "%s" % e

def dataPaginate(req,value,*args,**kwargs):
    try:
            if value.params == "" or value.params == "0": #remove 0 temp f#$k up
                cmd = "%s.objects.all()" % (value.klass)
            else:
                  cmd = "%s.objects.filter(%s)" % (value.klass,value.params) % kwargs

            if value.filterorder: cmd = "%s.order_by(\"%s\")" % (cmd,value.filterorder)
            data = eval(cmd)
            return {"paginate":paginated(req,data,prefix="%d" % value.id),"cmd":cmd}

    except Exception,e:
        return "%s" % e


def dataPaginatev2(req,value,kfilter={},paginate=True,*args,**kwargs):
    try:
            cmd = "%s.objects" % value.klass
            
            if len(kfilter) == 0:
                cmd = cmd+".all()"
            else:
                cmd = cmd+".filter(**%s)" % kfilter

            if value.exclude : cmd = cmd+".exclude(**%s)" % kwargs["exclude"]
            if value.filterorder : cmd = cmd+".order_by(\"%s\")" % value.filterorder 
            data = eval(cmd)
            p = paginated(req,data)
            #THANKS ADAM FOR SUPPORTING AGGREGATION
            if paginate :
                return {"paginate":paginated(req,data,prefix="%d" % value.id),"cmd":cmd}
            else: 
                return {"paginate":data,"cmd":cmd}

    except Exception,e:
        return "%s e %s" % (e,cmd)



