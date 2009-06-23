#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

""""
DEPENDENCIES: 
logger, contacts
"""

import re, os
import rapidsms
from rapidsms.parsers.bestmatch import BestMatch
from models import *
import gettext
import traceback
import string
from apps.smsforum.models import *
import apps.contacts.models as contacts_models
from apps.contacts.models import Contact
from apps.logger.models import *
from pygsm import gsmcodecs

MAX_LATIN_SMS_LEN = 160 
MAX_LATIN_BLAST_LEN = 140 # resere 20 chars for us
MAX_UCS2_SMS_LEN = 70 
MAX_UCS2_BLAST_LEN = 60 # reserve 10 chars for info

CMD_MESSAGE_MATCHER = re.compile(ur'^\s*([\.\*\#])\s*(\S+)?\s*',re.IGNORECASE)
         
#
# Module level translation calls so we don't have to prefix everything 
# so we don't have to prefix _t() with 'self'!!
#

# Mutable globals hack 'cause Python module globals are WHACK
_G = { 'SUPPORTED_LANGS': {
        # 'deb':u'Debug',
        'pul':u'Pulaar',
        'wol':u'Wolof',
        'dyu':u'Dyuola',
        'fre':u'Français',
        'eng':u'English',
    },
      'DEFAULT_LANG':'fre',
      'TRANSLATORS':dict()
}

def __init_translators():
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
__init_translators()


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
            # Dyuola
            ('ounoken', {'lang':'dyu','func':self.join}),
            ('karess', {'lang':'dyu','func':self.register_name}),
            ('oupour', {'lang':'dyu','func':self.leave}),
            ('rambenom', {'lang':'dyu','func':self.help}),
            # Debug calls ('deb' language==debug)
            ('djoin', {'lang':'deb','func':self.join}),
            ('rname', {'lang':'deb','func':self.register_name}),
            ('dleave', {'lang':'deb','func':self.leave}),
            ('dlang', {'lang':'deb','func':self.lang}),
            ('dcreate', {'lang':'eng','func':self.createvillage}),
            # French
            ('entrer', {'lang':'fre','func':self.join}),
            ('nom', {'lang':'fre','func':self.register_name}),
            ('quitter', {'lang':'fre','func':self.leave}),
            ('aide', {'lang':'fre','func':self.help}),
            # TODO: make best matcher smart about accents...
            ('créer', {'lang':'fre','func':self.createvillage}),
            ('creer', {'lang':'fre','func':self.createvillage}),
            # English
            ('join', {'lang':'eng','func':self.join}),
            ('name', {'lang':'eng','func':self.register_name}),
            ('leave', {'lang':'eng','func':self.leave}),
            ('language', {'lang':'eng','func':self.lang}),
            ('help', {'lang':'eng','func':self.help}),
            ('create', {'lang':'eng','func':self.createvillage}),
            ('member', {'lang':'eng','func':self.member}),
            ('citizens', {'lang':'eng','func':self.community_members}),
            ('remove', {'lang':'eng','func':self.destroy_community}),
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
    
    #####################
    # Message Lifecycle #
    #####################
    def parse(self, msg):
        self.debug("SMSFORUM:PARSE")

        msg.sender = contacts_models.ContactFromMessage(msg,self.router)
        self.info('Identified user: %r,%s with connections: %s', msg.sender, msg.sender.locale, \
                      ', '.join([repr(c) for c in msg.sender.channel_connections.all()]))
    
    def handle(self, msg):
        self.debug("SMSFORUM:HANDLE: %s" % msg.text)

        # check permissions
        if msg.sender.perm_ignore:
            self.debug('Ignoring sender: %s' % msg.sender.signature)
            return False

        if not msg.sender.can_send:
            self.debug('Sender: %s does no have receive perms' % msg.sender.signature)
            self.__reply(msg,'Message rejected. User does not have send perms')
        
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
            self.__reply(msg,"command-not-understood")
            return True

        # Now match the possible command to ones we know
        cmd_match=self.cmd_matcher.match(cmd,with_data=True)

        if len(cmd_match)==0:
            # no command match
            self.__reply(msg,"command-not-understood")
            return True

        if len(cmd_match)>1:
            # too many matches!
            self.__reply(msg, 'Command not understood. Did you mean one of: %(firsts)s or %(last)s?', \
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

    def outgoing(self, msg):
        # TODO
        # create a ForumMessage class
        # log messages with associated domain
        # report on dashboard
        pass
        

    ####################
    # Command Handlers #
    ####################
    def help(self, msg,arg=None):
        # TODO: grab senders language and translate based on that
        self.__reply(msg, "help with commands")
        return True

    def createvillage(self, msg, arg=None):
        self.debug("SMSFORUM:CREATEVILLAGE")        
        if arg is None or len(arg)<1:
            self.__reply(msg, "Please send a village name: #send 'village name'")
            return True
        else:
            village = arg

        if len(Village.objects.filter(name=village))!=0:
            self.__reply(msg, "The village %(village)s already exists.", {'village':village})
            return True
        try:
            # TODO: add administrator authentication
            ville = Village(name=village)
            ville.save()
            self.village_matcher.add_target((village,ville))
            self.__reply(msg, "village %(village)s created", {'village':village} )
        except:
            self.debug( traceback.format_exc() )
            traceback.print_exc()
            self.__reply(msg, "register-fail")

        return True
             
    def member(self,msg,arg=None):
        try:
            villages=VillagesForContact(msg.sender)
            if len(villages)==0:
                self.__reply(msg, "nothing to leave")
            else:
                village_names = ', '.join([v.name for v in villages])
                self.__reply(msg, "member-of %(village_names)s",
                             {"village_names":village_names})
        except:
            traceback.print_exc()
            self.debug( traceback.format_exc() )
            rsp= _st(msg.sender,"register-fail")
            self.debug(rsp)
            self.__reply(msg,rsp)
        return True

    def community_members(self,msg,arg=None):
        if arg is None or len(arg)==0:
            self.__reply(msg, "Missing name. Please send #citizens 'village'")
            return True

        villes=self.village_matcher.match(arg,with_data=True)
        if len(villes)==0:
            self.__reply(msg,msg.sender, "village-not-known")
            return True

        for name,ville in villes:
            members=[c.get_signature(max_len=10) for c in \
                         ville.flatten(klass=Contact)]
            self.__reply(msg, '%(name)s: %(citizens)s',
                         {'name':name, 'citizens':','.join(members)})
        return True

    def destroy_community(self,msg,arg=None):
         if arg is None or len(arg)==0:
            self.__reply(msg, "Missing name. Please send #destroy 'village'")
            return True

         try:
             # EXACT MATCH ONLY!
             ville=Village.objects.get(name=arg)
             ville.delete()
             self.village_matcher.remove_target(arg)
             self.__reply(msg, "The village '%(ville)s was removed.", {'ville': arg})
             return True
         except:
             rsp= _st(msg.sender,"village-not-known")
             self.debug(rsp)
             self.__reply(msg,rsp)
         return True

            
    def register_name(self,msg,arg=None):
        print arg
        if arg is None or len(arg)==0:
            self.__reply(msg,"name-register-success %(name)s",
                         {'name':msg.sender.signature})
            return True

        name=arg
        try:
            msg.sender.common_name = name
            msg.sender.save()
            rsp=_st(msg.sender, "name-register-success %(name)s") % {'name':msg.sender.common_name}
            self.__reply(msg,rsp)
        except:
            traceback.print_exc()
            self.debug( traceback.format_exc() )
            rsp= _st(msg.sender, "register-fail")
            self.debug(rsp)
            self.__reply(msg,rsp)

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
                    self.__reply(msg,resp)
                    return True
            
            # ok, here we got just one
            assert(len(villages)==1)
            msg.sender.add_to_group(villages[0])
            rsp=_st(msg.sender, "first-login") % {"village": village_names[0]}
            self.debug(rsp)
            self.__reply(msg,rsp)
        except:
            traceback.print_exc()
            self.debug( traceback.format_exc() )
            rsp=_st(msg.sender, "register-fail")
            self.debug(rsp)
            self.__reply(msg,rsp)
        return True
            
    def blast(self, msg):
        txt = msg.text
        try:
            sender = msg.sender

            # check for message length, and bounce messages that are too long
            # first is this a GSM (latin chars) or Unicode message?
            gsm_enc=True
            try:
                msg.text.encode('gsm')
            except:
                # it's unicode
                gsm_enc=False

            if (gsm_enc and len(txt)>MAX_LATIN_BLAST_LEN) or \
                    (not gsm_enc and len(txt)>MAX_UCS2_BLAST_LEN):
                rsp= _st(msg.sender, \
                             "%(msg_len)d: too long. Latin script max: %(max_latin)d. Unicode max: %(max_uni)s") % \
                             {
                    'msg_len': len(txt),
                    'max_latin': MAX_LATIN_BLAST_LEN,
                    'max_uni': MAX_UCS2_BLAST_LEN
                    } 
                self.__reply(msg,rsp)
                return True

            self.debug("SMSFORUM:BLAST")
            #find all reporters from the same location
            villages = VillagesForContact(sender)
            if len(villages)==0:
                rsp=_st(msg.sender, "You must join a village before sending messages")
                self.debug(rsp)
                self.__reply(msg,rsp)
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
            self.__reply(msg,rsp)
            
            # make message template for outbound so I can count size _after_ translation
            blast_tmpl=string.Template(_st(msg.sender, "%(txt)s - sent to [%(ville)s] from %(sender)s") % \
                { 'txt':txt, 'ville':ville.name, 'sender':'$sig'})

            #add signature
            tmpl_len=len(blast_tmpl.template)-4  # -4 accounts from sig placeholder ('$')
            max_sig=MAX_LATIN_SMS_LEN-tmpl_len
            if not gsm_enc:
                max_sig=MAX_UCS2_SMS_LEN-tmpl_len

            sig=sender.get_signature(max_len=max_sig,for_message=msg)
            announcement = blast_tmpl.substitute(sig=sig.replace('$','$$'))

            # now iterate every member of the group we are broadcasting
            # to, and queue up the same message to each of them
            for recipient in recipients:
                if recipient != msg.sender and recipient.can_receive:
                    recipient.send_to(announcement) 
            village_names = village_names.strip()
            self.debug( _st(msg.sender, "success! %(villes)s recvd msg: %(txt)s") % { 'villes':village_names,'txt':txt})
            return True
        except:
            traceback.print_exc()
            self.debug( traceback.format_exc() )
            self.__reply(msg, "blast-fail")
        return True

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
                self.__reply(msg, "leave-success",
                             { "village": ','.join(names)})
            else:
                self.__reply(msg, "nothing to leave")
        except:
            # something went wrong - at the
            # moment, we don't care what
            traceback.print_exc()
            self.debug( traceback.format_exc() )
            self.__reply(msg, "leave-fail")

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
            self.__reply(msg,resp)
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
            self.__reply(msg,resp)
            return True       
        else: 
            # invalid lang code, send them a list
            return _return_all_langs()


    #
    # Private helpers
    # 
    def __reply(self,msg,reply_text,format_values=None):
        """
        Formats string for response for message's sender 
        the message's associated sender.

        """
        if format_values is not None:
            reply_text=_st(msg.sender,reply_text) % format_values
        
        msg.sender.send_response_to(msg,reply_text)
        
    
    def __suggest_villages(self,msg):
        """helper to send informative messages"""
        # pick some names from the DB
        village_names = [v.name for v in Village.objects.all()[:3]]
        if len(village_names) == 0:
            village_names = _st(msg.sender,"village name")
        else: 
            village_names=', '.join(village_names)
        self.__reply(msg,"village does not exist", {"village_names": village_names})
        return True

    def __loadFixtures(self):
        pass

    def __log_incoming_message(self,msg,domain):
        msg.persistent_msg.domain = domain
        msg.persistent_msg.save()

