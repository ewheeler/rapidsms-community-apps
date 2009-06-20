#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

""""
DEPENDENCIES: 
logger, contacts
"""

import re, os
import rapidsms
from rapidsms.parsers import Matcher
from rapidsms.message import Message
from rapidsms.parsers.bestmatch import BestMatch
from models import *
import gettext
import traceback
import string

from apps.smsforum.models import *
from apps.contacts.models import *
from apps.logger.models import *

MAX_BLAST_CHARS=140
CMD_MESSAGE_MATCHER=re.compile(ur'^\s*([\.\*\#])\s*(\S+)?\s*',re.IGNORECASE)
         
#
# Module level translation calls so we don't have to prefix everything 
# so we don't have to prefix _t() with 'self'!!
#

# Mutable globals hack 'cause Python module globals are WHACK
_G= { 'SUPPORTED_LANGS': {
        # 'deb':u'Debug',
        'eng':u'English',
        'fre':u'Français',
        'pul':u'Pulaar',
        'wol':u'Wolof',
    },
      'DEFAULT_LANG':'fre',
      'TRANSLATORS':dict()
}

def _initTranslators():
    path = os.path.join(os.path.dirname(__file__),"locale")
    for lang,name in _G['SUPPORTED_LANGS'].items():
        trans = gettext.translation('messages',path,[lang,_G['DEFAULT_LANG']])
        _G['TRANSLATORS'].update( {lang:trans} )

def _t(text, locale=None):
    """translate text with default language"""
    translator=_G['TRANSLATORS'][_G['DEFAULT_LANG']]
    if locale in _G['TRANSLATORS']:
        translator=_G['TRANSLATORS'][locale]
    return translator.gettext(text)

def _st(sender,text):
    """translate a message for the given sender"""
    # TODO: handle fall back from say eng_US to eng
    # AND mappings from old-stylie two letter ('en') to 
    # new hotness 3-letter codes 'eng'
    return _t(text,locale=sender.locale)

# init them translators!    
_initTranslators()


#
# App class
#

class App(rapidsms.app.App):
    def __init__(self, router):
        rapidsms.app.App.__init__(self, router)

        # command target. ToDo--get names from gettext...
        # needs to be here so that 'self' has meaning.
        # could also do the hasattr thing when calling instead
        self.cmd_targets = [ 
            # English
            ('join', {'lang':'eng','func':self.join}),
            ('name', {'lang':'eng','func':self.register_name}),
            ('leave', {'lang':'eng','func':self.leave}),
            ('language', {'lang':'eng','func':self.lang}),
            ('help', {'lang':'eng','func':self.help}),
            ('create', {'lang':'eng','func':self.createvillage}),
            ('member', {'lang':'eng','func':self.member}),
            # French
            ('entrer', {'lang':'fre','func':self.join}),
            ('nom', {'lang':'fre','func':self.register_name}),
            ('quitter', {'lang':'fre','func':self.leave}),
            ('aide', {'lang':'fre','func':self.help}),
            # TODO: make best matcher smart about accents...
            ('créer', {'lang':'fre','func':self.createvillage}),
            ('creer', {'lang':'fre','func':self.createvillage}),
            # Pulaar
            ('naalde', {'lang':'pul','func':self.join}),
            ('yettoode', {'lang':'pul','func':self.register_name}),
            ('yaltude', {'lang':'pul','func':self.leave}),
            ('help', {'lang':'pul','func':self.help}),
            # Wolof
            ('boole', {'lang':'wol','func':self.join}),
            ('yokk', {'lang':'wol','func':self.join}),
            ('duggu', {'lang':'wol','func':self.join}),
            ('sant', {'lang':'wol','func':self.register_name}),
            # spaces are bad!! Keywords must be one word--so comel case this one
            ('maaNgiTudd', {'lang':'wol','func':self.register_name}), 
            ('genn', {'lang':'wol','func':self.leave}),
            ('help', {'lang':'wol','func':self.help}),
            # Debug calls ('deb' language==debug)
            ('djoin', {'lang':'deb','func':self.join}),
            ('rname', {'lang':'deb','func':self.register_name}),
            ('dleave', {'lang':'deb','func':self.leave}),
            ('dlang', {'lang':'deb','func':self.lang}),
            ('dcreate', {'lang':'eng','func':self.createvillage})
            ]
        
        self.cmd_matcher=BestMatch(self.cmd_targets)
        villes=[(v.name,v) for v in Village.objects.all()]
        self.village_matcher=BestMatch(villes, ignore_prefixes=['keur'])
        # swap dict so that we send in (name,code) tuples rather than (code,name
        self.lang_matcher=BestMatch([
                (name,code) for code,name in _G['SUPPORTED_LANGS'].items()
                ])

    def start(self):
        self.__loadFixtures()
    
    def parse(self, msg):
        self.debug("SMSFORUM:PARSE")

        msg.sender = ContactFromMessage(msg,self.router)
        self.info('Identified user: %r,%s with connections: %s', msg.sender, msg.sender.locale, \
                      ', '.join([repr(c) for c in msg.sender.channel_connections.all()]))
    
    def handle(self, msg):
        self.debug("SMSFORUM:HANDLE: %s" % msg.text)

        # check permissions
        if msg.sender.perm_ignore:
            self.debug('Ignoring sender: %s' % sender.signature)
            return False

        if not msg.sender.can_send:
            self.debug('Sender: %s does no have receive perms' % sender.signature)
            msg.sender.send_to(_st(msg.sender, 'Message rejected. User does not have send perms'))
        
        # Ok, we're all good, start processing
        msg.sender.sent_message_accepted(msg)
        msg_text=msg.text.strip()

        #see if it is a command
        cmd=None
        msg_match=CMD_MESSAGE_MATCHER.match(msg_text)
        if msg_match is not None:
            cmd=msg_match.groups()[1]
        else:
            # it's a blast message (not a command)
            self.blast(msg)
            return True

        # Command processing
        if cmd is None:
            #user tried to send some sort of command (a message with .,#, or *, but nothing after)
            msg.sender.send_to(_st(msg.sender, "command-not-understood"))
            return True

        # Now match the possible command to ones we know
        cmd_match=self.cmd_matcher.match(cmd,with_data=True)

        if len(cmd_match)==0:
            # no command match
            msg.sender.send_to(_st(msg.sender, "command-not-understood"))
            return True

        if len(cmd_match)>1:
            # too many matches!
            msg.sender.send_to(_st(msg.sender, 'Command not understood. Did you mean one of: %(firsts)s or %(last)s?') %\
                              { 'firsts':', '.join([t[0] for t in cmd_match[:-1]]),
                                'last':cmd_match[-1:][0][0]})
            return True
        #
        # Ok! We got a real command
        #
        cmd,data=cmd_match[0]
        arg=msg_text[msg_match.end():]

        # set the senders default language, if not sent
        if msg.sender.locale is None:
            msg.sender.locale=data['lang']
            msg.sender.save()
        return data['func'](msg,arg=arg)
        
    def help(self, msg,arg=None):
        # TODO: grab senders language and translate based on that
        msg.sender.send_to(_st(msg.sender, "help with commands"))
        return True

    def createvillage(self, msg, arg=None):
        self.debug("SMSFORUM:CREATEVILLAGE")        
        if arg is None or len(arg)<1:
            msg.sender.send_to(_st(msg.sender, "Please send a village name: #send 'village name'"))
            return True
        else:
            village = arg

        try:
            # TODO: add administrator authentication

            ville = Village.objects.get_or_create(name=village)
            self.village_matcher.add_target((village,ville))
            msg.sender.send_to(_st(msg.sender, "village %s created") % village)
            # TODO: remove this for production
        except:
            traceback.print_exc()
            msg.sender.send_to(_st(msg.sender, "register-fail"))

        return True
             
    def member(self,msg,arg=None):
        # TODO: process argument to say if you
        # are a member of _that_ village only
        try:
            villages=VillagesForContact(msg.sender)
            if len(villages)==0:
                msg.sender.send_to( _st(msg.sender, "nothing to leave"))
            else:
                village_names = ', '.join([v.name for v in villages])
                msg.sender.send_to(_st(msg.sender, "member-of %(village_names)s") \
                                       % {"village_names":village_names})
        except:
            traceback.print_exc()
            rsp= _st(msg.sender,"register-fail")
            self.debug(rsp)
            msg.sender.send_to(rsp)
        return True
            
    def register_name(self,msg,arg=None):
        print arg
        if arg is None or len(arg)==0:
            msg.sender.send_to(_st(msg.sender,
                "name-register-success %(name)s") % {'name':msg.sender.signature})
            return True

        name=arg
        try:
            msg.sender.common_name = name
            msg.sender.save()
            rsp=_st(msg.sender, "name-register-success %(name)s") % {'name':msg.sender.common_name}
            msg.sender.send_to(rsp)
        except:
            traceback.print_exc()
            rsp= _st(msg.sender, "register-fail")
            self.debug(rsp)
            msg.sender.send_to(rsp)

        return True

    def __suggest_villages(self,msg):
        """helper to send informative messages"""
        # pick some names from the DB
        village_names = [v.name for v in Village.objects.all()[:3]]
        if len(village_names) == 0:
            village_names = _st(msg.sender,"village name")
        else: 
            village_names=', '.join(village_names)
        resp =  _st(msg.sender, "village does not exist") % {"village_names": village_names}
        msg.sender.send_to(resp)
        return True

    def join(self,msg,arg=None):
        suggest=False
        if arg is None or len(arg)==0:
            return self.__suggest_villages(msg)
        else:
            village=arg

        try:
            matched_villes=self.village_matcher.match(village,with_data=True)
            # send helpful message if 0 or more than 1 found
            num_villes=len(matched_villes)
            # unzip data from names if can
            if num_villes>0:
                village_names,villages=zip(*matched_villes)
            if num_villes==0 or num_villes>1:
                if num_villes==0:
                    return self.__suggest_villages(msg)
                else:
                    # use all hit targets
                    resp=_st(msg.sender, "village does not exist") % \
                        {"village_names": ', '.join(village_names)}
                    msg.sender.send_to(resp)
                    return True

            # ok, here we got just one
            msg.sender.add_to_group(villages[0])
            rsp=_st(msg.sender, "first-login") % {"village": village_names[0]}
            self.debug(rsp)
            msg.sender.send_to(rsp)
        except:
            traceback.print_exc()
            rsp=_st(msg.sender, "register-fail")
            self.debug(rsp)
            msg.sender.send_to(rsp)
        return True
            
    def blast(self, msg):
        txt = msg.text
        try:
            sender = msg.sender

            # check for message length, and bounce messages that are too long
            if len(txt) > MAX_BLAST_CHARS:
                rsp= _st(msg.sender, "Message was not delivered. Please send less than %(max_chars)d characters.") % {'max_chars': MAX_BLAST_CHARS} 
                msg.sender.send_to(rsp)
                return True

            self.debug("SMSFORUM:BLAST")
            #find all reporters from the same location
            villages = VillagesForContact(sender)
            if len(villages)==0:
                rsp=_st(msg.sender, "You must join a village before sending messages")
                self.debug(rsp)
                msg.sender.send_to(rsp)
                return True

            recipients=set()
            village_names = ''
            for ville in villages:
                village_names = ("%s %s") % (village_names, ville.name) 
                recipients.update(ville.flatten(klass=Contact))

            # respond to sender first because the delay between now and the last recipient
            # can be long
            rsp= _st(msg.sender, "success! %(villes)s recvd msg: %(txt)s") % {'villes':village_names,'txt':txt} 
            self.debug('REPSONSE TO BLASTER: %s' % rsp)
            msg.sender.send_to(rsp)
            
            # make message template for outbound
            rsp_template=string.Template(_st(msg.sender, "%(txt)s - sent to [%(ville)s] from %(sender)s") % \
                { 'txt':txt, 'ville':ville.name, 'sender':'$sig'})
            # now iterate every member of the group we are broadcasting
            # to, and queue up the same message to each of them

            for recipient in recipients:
                if recipient != msg.sender and recipient.can_receive:
                    #add signature
                    announcement = rsp_template.substitute(sig=sender.signature.replace('$','$$'))
                    #todo: limit chars to 1 txt message?
                    recipient.send_to(announcement) 
            village_names = village_names.strip()
            self.debug( _st(msg.sender, "success! %(villes)s recvd msg: %(txt)s") % { 'villes':village_names,'txt':txt})
            return True
        except:
            traceback.print_exc()
            msg.sender.send_to(_st(msg.sender, "blast-fail"))
        return True

    def __log_incoming_message(self,msg,domain):
        msg.persistent_msg.domain = domain
        msg.persistent_msg.save()

    def leave(self,msg,arg=None):
        self.debug("SMSFORUM:LEAVE: %s" % arg)
        try:
            villages=[]
            if arg is not None and len(arg)>0:
                village_tupes=self.village_matcher.match(arg,with_data=True)
                if len(village_tupes)>0:
                    villages=zip(*village_tupes)[1] # the objects
            else:
                villages=VillagesForContact(msg.sender)
            if len(villages)>0:
                names=list()
                for ville in villages:
                    msg.sender.remove_from_group(ville)
                    names.append(ville.name)
                msg.sender.send_to(_st(msg.sender, "leave-success") % \
                                       { "village": ','.join(names)})
            else:
                msg.sender.send_to( _st(msg.sender, "nothing to leave"))
        except:
            # something went wrong - at the
            # moment, we don't care what
            traceback.print_exc()
            msg.sender.send_to(_st(msg.sender, "leave-fail"))

        return True

    def lang(self,msg,arg=None):
        name=arg
        self.debug("SMSFORUM:LANG:Current locale: %s" % msg.sender.locale)
        
        def _return_all_langs():
            # return available langs
            langs_sorted=_G['SUPPORTED_LANGS'].values()
            langs_sorted.sort()
            resp=_st(msg.sender, "supported-langs: %(langs)s") % \
                { 'langs':', '.join(langs_sorted)}
            msg.sender.send_to(resp)
            return True

        if len(name)==0:
            return _return_all_langs()
        
        # see if we have that language
        langs=self.lang_matcher.match(name.strip(),with_data=True)
        if len(langs)==1:
            name,code=langs[0]
            msg.sender.locale=code
            msg.sender.save()
            resp = _st(msg.sender, "lang-set %(lang_code)s") % { 'lang_code': name }
            msg.sender.send_to(resp)
            return True       
        else: 
            # invalid lang code, send them a list
            return _return_all_langs()

    def __loadFixtures(self):
        pass

    def outgoing(self, msg):
        # TODO
        # create a ForumMessage class
        # log messages with associated domain
        # report on dashboard
        pass
        
                        
