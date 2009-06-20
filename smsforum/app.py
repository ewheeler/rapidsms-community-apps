#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

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

MAX_BLAST_CHARS=140
CMD_MESSAGE_MATCHER=re.compile(ur'^\s*([\.\*\#])\s*(\S+)?\s*',re.IGNORECASE)
         
#
# Module level translation calls so we don't have to prefix everything 
# so we don't have to prefix _t() with 'self'!!
#

# Mutable globals hack 'cause Python module globals are WHACK
_G= { 'SUPPORTED_LANGS': {
        'eng':u'English',
        'fre':u'Français',
        'pul':u'Pulaar',
        'wol':u'Wolof',
        'deb':u'Debug'
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
    def help(self, msg,args):
        # TODO: grab senders language and translate based on that
        msg.sender.send_to(_st(msg.sender, "help with commands"))

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
            # French
            ('entrer', {'lang':'fre','func':self.join}),
            ('nom', {'lang':'fre','func':self.register_name}),
            ('quitter', {'lang':'fre','func':self.leave}),
            ('aide', {'lang':'fre','func':self.help}),
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
            ('maa ngi tudd', {'lang':'wol','func':self.register_name}),
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
        villes=[v.name for v in Village.objects.all()]
        self.village_matcher=BestMatch(villes, ignore_prefixes=['keur'])
        # swap dict so that we send in (name,code) tuples rather than (code,name)
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
        # strip command from the string to get args
        args=msg_text[msg_match.end():]

        # set the senders default language, if not sent
        if msg.sender.locale is None:
            msg.sender.locale=data['lang']
            msg.sender.save()
        return data['func'](msg,args)
        
      
    # admin utility!
    def createvillage(self, msg, village):
        village = village.strip()

        try:
            # TODO: add administrator authentication
            self.debug("SMSFORUM:CREATEVILLAGE")
            ville = Village.objects.get_or_create(name=village)
            self.village_matcher.add_target(village)
            msg.sender.send_to(_st(msg.sender, "village %s created") % village)
            # TODO: remove this for production
        except:
            traceback.print_exc()
            msg.sender.send_to(_st(msg.sender, "register-fail"))

        return True
             
    def register_name(self, msg, family_name):
        try:
            msg.sender.family_name = family_name
            msg.sender.save()
            rsp=( _st(msg.sender, "name-register-success %(name)s") % {'name':family_name})
            msg.sender.send_to(rsp)
        except:
            traceback.print_exc()
            rsp= _st(msg.sender, "register-fail")
            self.debug(rsp)
            msg.sender.send_to(rsp)

        return True

    def join(self, msg, village):
        try:
            matched_villes=self.village_matcher.match(village)
            # send helpful message if 0 or more than 1 found
            num_villes=len(matched_villes)
            if num_villes==0 or num_villes>1:
                if num_villes==0:
                    # pick some names from the DB
                    village_names = [v.name for v in Village.objects.all()[:3]]
                    if len(village_names) == 0:
                        village_names = _st(msg.sender,"village name")
                    else: 
                        village_names=', '.join(village_names)
                else:
                    # use all hit targets
                    village_names=', '.join(matched_villes)
                resp =  _st(msg.sender, "village does not exist") % {"village_names": village_names}
                msg.sender.send_to(resp)
                return True

            # ok, here we got just one
            rs=Village.objects.filter(name=matched_villes[0])
            if len(rs) != 1:
                # huh? that's supposed to be Unique
                raise Exception('Multiple entries for village: %s' % matched_villes[0])

            ville=rs[0]
            msg.sender.add_to_group(ville)
            rsp=_st(msg.sender, "first-login") % {"village": ville.name } 
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

    def leave(self, msg,arg):
        try:
            self.debug("SMSFORUM:LEAVE")
            if msg.sender is not None:
                villages=VillagesForContact(msg.sender)
                if len(villages)>0:
                    #default to deleting all persistent connections with the same identity
                    #we can always come back later and make sure we are deleting the right backend
                    names=list()
                    for ville in villages:
                        msg.sender.remove_from_group(ville)
                        names.append(ville.name)
                    msg.sender.send_to(_st(msg.sender, "leave-success") % \
                                           { "village": ','.join(names)})
                    return True
            msg.sender.send_to( _st(msg.sender, "nothing to leave"))
            return True
        # something went wrong - at the
        # moment, we don't care what
        except:
            traceback.print_exc()
            msg.sender.send_to(_st(msg.sender, "leave-fail"))

        return True

    def lang(self, msg, name):
        # TODO: make this a decorator to be used in all functions
        # so that users don't have to register in order to get going
        self.debug("SMSFORUM:LANG:Current locale: %s" % msg.sender.locale)
        if name=='':
            # return current lang
            lang=msg.sender.locale
            if lang is None:
                lang=_G['DEFAULT_LANG']
            resp=_st(msg.sender, "current-lang %(lang)s") % \
                           { 'lang':_G['SUPPORTED_LANGS'][lang]}
            msg.sender.send_to(resp)
            return True
        
        # see if we have that language
        langs=self.lang_matcher.match(name.strip(),with_data=True)
        if len(langs)==1:
            name,code=langs[0]
            msg.sender.locale=code
            msg.sender.save()
            resp = _st(msg.sender, "lang-set %(lang_code)s") % { 'lang_code': name }
                   
        # invalid language code. don't do
        # anything, just send an error message
        else: 
            resp = _st(msg.sender, "bad-lang")
        
        self.debug(resp)        
        msg.sender.send_to(resp)

        return True


    def __loadFixtures(self):
        pass



                        
