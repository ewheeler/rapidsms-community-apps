#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

""""
DEPENDENCIES: 
logger, contacts
"""

import re, os
import rapidsms
from rapidsms.parsers.bestmatch import BestMatch, MultiMatch
import gettext
import traceback
from apps.smsforum.models import Village, villages_for_contact
import apps.contacts.models as contacts_models
from apps.contacts.models import Contact, contact_from_message
from apps.logger.models import CodeSet, Code
from pygsm import gsmcodecs

MAX_LATIN_SMS_LEN = 160 
MAX_LATIN_BLAST_LEN = MAX_LATIN_SMS_LEN - 20 # resere 20 chars for us
MAX_UCS2_SMS_LEN = 70 
MAX_UCS2_BLAST_LEN = MAX_UCS2_SMS_LEN - 10 # reserve 10 chars for info
MAX_VILLAGE_NAME_LEN = 40
MAX_CONTACT_NAME_LEN = 30

CMD_MARKER=ur'(?:[\.\*\#]|(?:123))'
DM_MESSAGE_MATCHER = re.compile(ur'^\s*'+CMD_MARKER+'(.+?)'+ \
                                    CMD_MARKER+'\s*(.+)?', re.IGNORECASE)
CMD_MESSAGE_MATCHER = re.compile(ur'^\s*'+CMD_MARKER+'\s*(\S+)?(.+)?',re.IGNORECASE)


         
#
# Module level translation calls so we don't have to prefix everything 
# so we don't have to prefix _t() with 'self'!!
#

# Mutable globals hack 'cause Python module globals are WHACK
_G = { 'SUPPORTED_LANGS': {
        # 'deb':u'Debug',
        'pul':u'Pulaar',
        'wol':u'Wolof',
        'dyu':u'Joola',
        'fr':u'Français',
        'en':u'English',
    },
      'DEFAULT_LANG':'fr',
      'TRANSLATORS':dict()
}

def __init_translators():
    path = os.path.join(os.path.dirname(__file__),"locale")
    for lang,name in _G['SUPPORTED_LANGS'].items():
        trans = gettext.translation('django',path,[lang,_G['DEFAULT_LANG']])
        _G['TRANSLATORS'].update( {lang:trans} )

def _t(locale, text):
    """translate text with default language"""
    translator=_G['TRANSLATORS'][_G['DEFAULT_LANG']]
    if locale in _G['TRANSLATORS']:
        translator=_G['TRANSLATORS'][locale]
    return translator.ugettext(text)

def _st(sender,text):
    """translate a message for the given sender"""
    # TODO: handle fall back from say eng_US to eng
    # AND mappings from old-stylie two letter ('en') to 
    # new hotness 3-letter codes 'eng'
    return _t(sender.locale, text)

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
            ('help-pul', {'lang':'pul','func':self.help}),
            # Wolof
            ('boole', {'lang':'wol','func':self.join}),
            ('yokk', {'lang':'wol','func':self.join}),
            ('duggu', {'lang':'wol','func':self.join}),
            ('genn', {'lang':'wol','func':self.leave}),
            ('sant', {'lang':'wol','func':self.register_name}),
            ('tur', {'lang':'wol','func':self.register_name}),
            ('help-wol', {'lang':'wol','func':self.help}),
            # Dyuola    
            ('unoken', {'lang':'dyu','func':self.join}),
            ('ounoken', {'lang':'dyu','func':self.join}),
            ('karees', {'lang':'dyu','func':self.register_name}),
            ('karess', {'lang':'dyu','func':self.register_name}),
            ('upur', {'lang':'dyu','func':self.leave}),
            ('oupour', {'lang':'dyu','func':self.leave}),
            ('rambenom', {'lang':'dyu','func':self.help}),
            ('ukaana', {'lang':'dyu','func':self.createvillage}),
            # Debug calls ('deb' language==debug)
            #('djoin', {'lang':'deb','func':self.join}),
            #('rname', {'lang':'deb','func':self.register_name}),
            #('dleave', {'lang':'deb','func':self.leave}),
            #('dlang', {'lang':'deb','func':self.lang}),
            #('dcreate', {'lang':'deb','func':self.createvillage}),
            # French
            ('entrer', {'lang':'fr','func':self.join}),
            ('nom', {'lang':'fr','func':self.register_name}),
            ('quitter', {'lang':'fr','func':self.leave}),
            ('aide', {'lang':'fr','func':self.help}),
            # TODO: make best matcher smart about accents...
            ('créer', {'lang':'fr','func':self.createvillage}),
            ('creer', {'lang':'fr','func':self.createvillage}),
            # English
            ('join', {'lang':'en','func':self.join}),
            ('name', {'lang':'en','func':self.register_name}),
            ('leave', {'lang':'en','func':self.leave}),
            ('language', {'lang':'en','func':self.lang}),
            ('help', {'lang':'en','func':self.help}),
            ('create', {'lang':'en','func':self.createvillage}),
            ('member', {'lang':'en','func':self.member}),
            ('citizens', {'lang':'en','func':self.community_members}),
            ('remove', {'lang':'en','func':self.destroy_community}),
            ]
        
        self.cmd_matcher=BestMatch(self.cmd_targets)
        villes=[(v.name, v) for v in Village.objects.all()]
        self.village_matcher=BestMatch(villes, ignore_prefixes=['keur'])
        # swap dict so that we send in (name,code) tuples rather than (code,name
        self.lang_matcher=BestMatch([
                (name,code) for code,name in _G['SUPPORTED_LANGS'].items()
                ])
        
        """ TODO: move this to fixture - just for testing right now! """
        s = CodeSet.objects.get_or_create(name="TOSTAN_CODE")[0]
        Code.objects.get_or_create(set=s, name="code1", slug="1")
        Code.objects.get_or_create(set=s, name="code2", slug="2")
        Code.objects.get_or_create(set=s, name="code3", slug="3")
        f = CodeSet.objects.get_or_create(name="FLAGGED_CODE")[0]
        Code.objects.get_or_create(set=f, name="flagged", slug="True")


    def start(self):
        self.__loadFixtures()
    
    #####################
    # Message Lifecycle #
    #####################
    def parse(self, msg):

        msg.sender = contact_from_message(msg,self.router)
        self.info('Identified user: %r,%s with connections: %s', msg.sender, msg.sender.locale, \
                      ', '.join([repr(c) for c in msg.sender.channel_connections.all()]))
    
    def handle(self, msg):
        self.__log_incoming_message(msg, villages_for_contact(msg.sender))
        self.debug("In handle smsforums: %s" % msg.text)
        
        # check permissions
        if msg.sender.perm_ignore:
            self.debug('Ignoring sender: %s' % msg.sender.signature)
            return False

        if not msg.sender.can_send:
            self.debug('Sender: %s does no have receive perms' % msg.sender.signature)
            self.__reply(msg,'inbound-message_rejected')
        
        # Ok, we're all good, start processing
        msg.sender.sent_message_accepted(msg)
        
        #
        # Now we figure out if it's a direct message, a command, or a blast
        #
        # ok, this is a little weird, but stay with me.
        # commands start with '.' '*' or '#'--the cmd markers. e.g. '.join <something>'
        # addresses are of form cmd_marker address cmd_mark--e.g. '.jeff. hello'
        #
        is_command=False
        is_dm=False
        cmd=None
        address=None
        rest=None

        # check for direct message first
        m=DM_MESSAGE_MATCHER.match(msg.text)
        if m is not None:
            address=m.group(1).strip()
            rest=m.group(2)
            if rest is not None:
                rest=rest.strip()
            return self.blast_direct(msg,address,rest)
        
        # are we a command?
        m=CMD_MESSAGE_MATCHER.match(msg.text)
        if m is None:
            # we are a blast
            return self.blast(msg)

        # we must be a command
        cmd,rest=m.groups()
        if cmd is None:
            #user tried to send some sort of command (a message with .,#, or *, but nothing after)
            self.__reply(msg,"command-not-understood")
            return True
        else:
            cmd=cmd.strip()
        
        if rest is not None:
            rest=rest.strip()

        # Now match the possible command to ones we know
        cmd_match=self.cmd_matcher.match(cmd,with_data=True)

        if len(cmd_match)==0:
            # no command match
            self.__reply(msg,"command-not-understood")
            return True

        if len(cmd_match)>1:
            # too many matches!
            self.__reply(msg, 'command-not-understood %(sug_1)s %(sug_rest)s', \
                              { 'sug_1':', '.join([t[0] for t in cmd_match[:-1]]),
                                'sug_rest':cmd_match[-1:][0][0]})
            return True
        #
        # Ok! We got a real command
        #
        cmd,data=cmd_match[0]
        #arg=msg_text[msg_match.end():]

        # set the senders default language, if not sent
        if msg.sender.locale is None:
            msg.sender.locale=data['lang']
            msg.sender.save()
        return data['func'](msg,arg=rest)

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
        if arg is not None and len(arg)>0:
            # see if it is a language and send help 
            # for that lang
            langs=self.lang_matcher.match(arg,with_data=True)
            if len(langs)==1:
                self.__reply(msg, "help-with-commands_%s" % langs[0][1])
                return True
            else:
                # send the list of available langs by passing
                # to the 'lang' command handler
                return self.lang(msg)
            
        self.__reply(msg, "help-with-commands")
        return True

    def createvillage(self, msg, arg=None):
        self.debug("SMSFORUM:CREATEVILLAGE")        
        if arg is None or len(arg)<1:
            self.__reply(msg, "create-village-fail_no-village-name")
            return True
        else:
            village = arg

        if len(Village.objects.filter(name=village)) != 0:
            self.__reply(msg, "create-village-fail_village-already-exists %(village)s", {'village':village})
            return True
        try:
            # TODO: add administrator authentication
            if len(village) > MAX_VILLAGE_NAME_LEN:
                self.__reply(msg, "create-village-fail_name-too-long %(village)s %(max_char)d", \
                             {'village':village, 'max_char':MAX_VILLAGE_NAME_LEN} )
                return True
            ville = Village(name=village)
            ville.save()
            self.village_matcher.add_target((village,ville))
            self.__reply(msg, "create-village-success %(village)s", {'village':village} )
        except:
            self.debug( traceback.format_exc() )
            traceback.print_exc()
            self.__reply(msg, "internal-error")

        return True
             
    def member(self,msg,arg=None):
        try:
            villages=villages_for_contact(msg.sender)
            if len(villages)==0:
                self.__reply(msg, "member-fail_not-member-of-village")
            else:
                village_names = ', '.join([v.name for v in villages])
                txt = "member-success %(village_names)s"
                if len(villages)>5: 
                    villages = villages[0:5]
                    txt = "member-success_long-list %(village_names)s"
                self.__reply(msg, txt, {"village_names":village_names})
        except:
            traceback.print_exc()
            self.debug( traceback.format_exc() )
            rsp= _st(msg.sender,"internal-error")
            self.debug(rsp)
            self.__reply(msg,rsp)
        return True

    def community_members(self,msg,arg=None):
        if arg is None or len(arg)==0:
            self.__reply(msg, "citizens-fail_no-village")
            return True

        villes=self.village_matcher.match(arg,with_data=True)
        if len(villes)==0:
            self.__reply(msg, "village-not-known %(unknown)s", {'unknown':arg})
            return True

        for name,ville in villes:
            members=[c.get_signature(max_len=10) for c in \
                         ville.flatten(klass=Contact)]
            if len(members)>20: 
                members = members[0:20]
                txt = 'citizens-success_long-list %(village)s %(citizens)s'
            else:
                txt = 'citizens-success %(village)s %(citizens)s'
                
            self.__reply(msg, txt, {'village':name, 'citizens':','.join(members)})
        return True

    def destroy_community(self,msg,arg=None):
         if arg is None or len(arg)==0:
            self.__reply(msg, "remove-fail_no-village")
            return True

         try:
             # EXACT MATCH ONLY!
             ville=Village.objects.get(name=arg)
             ville.delete()
             self.village_matcher.remove_target(arg)
             self.__reply(msg, "remove-success %(village)s", {'village': arg})
             return True
         except:
             rsp= _st(msg.sender,"village-not-known %(unknown)s") % {'unknown':arg} 
             self.debug(rsp)
             self.__reply(msg,rsp)
         return True

            
    def register_name(self,msg,arg=None):
        if arg is None or len(arg)==0:
            self.__reply(msg,"name-acknowledge %(name)s",
                         {'name':msg.sender.common_name})
            return True

        name=arg
        try:
            if len(name) > MAX_CONTACT_NAME_LEN:
                self.__reply(msg, "name-register-fail_name-too-long %(name)s %(max_char)d", \
                             {'name':name, 'max_char':MAX_CONTACT_NAME_LEN} )
                return True
            msg.sender.common_name = name
            msg.sender.save()
            rsp=_st(msg.sender, "name-register-success %(name)s") % {'name':msg.sender.common_name}
            self.__reply(msg,rsp)
        except:
            traceback.print_exc()
            self.debug( traceback.format_exc() )
            rsp= _st(msg.sender, "internal-error")
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
                    rsp=_st(msg.sender, "village-not-found %(suggested)s") % \
                        {"suggested": ', '.join(village_names)}
                    self.__reply(msg,rsp)
                    return True
            
            # ok, here we got just one
            assert(len(villages)==1)
            msg.sender.add_to_parent(villages[0])
            rsp=_st(msg.sender, "join-success %(village)s") % {"village": village_names[0]}
            self.debug(rsp)
            self.__reply(msg,rsp)
        except:
            traceback.print_exc()
            self.debug( traceback.format_exc() )
            rsp=_st(msg.sender, "internal-error")
            self.debug(rsp)
            self.__reply(msg,rsp)
        return True
            
    def blast_direct(self, msg, address, text):
        """
        find the matching people, groups. 
         
        Consider only matches that return ONE result!
        
        Otherwise people might accidentally send messages
        far wider than expected!
        
        The direct messaging to Contacts currently uses
        'common_name' which is not guaranteed unique,
        so if two people have the same name, the returned set
        will never be unique, and you will not be allowed to
        send to them.
        
        a system that wants to really implement Twitter like
        DM needs to either enforce uniqueness on common_name
        or use the 'unique_id' field in stead.
        
        Either way people will need to register a 'username'
        like handle in the field used for the match.
        
        """

        contacts=[(c.common_name, c) for c in Contact.objects.all()]
        cont_matcher=BestMatch(targets=contacts)
        found=MultiMatch(self.village_matcher,cont_matcher).\
            match(address,with_data=True)
        
        if len(found)==0:
            self.__reply(
                msg,
                'direct-blast-fail_recipient-not-found %(recipient)s',
                {'recipient':address}
                )
        elif len(found)>1:
            names,objs=zip(*found)
            self.__reply(
                msg,
                'direct-blast-fail_too-many-recipients %(recip_1)s and %(recip_rest)s',
                { 'recip_1':names[0], 'recip_rest': ', '.join(names[1:])}
                )
        else:
            # got one person or village!
            name,obj=found[0] # found is an array of tuples (name,obj)

            # prep the outbound message
            ok,out_text,enc=self.__prep_blast_message(msg,text,[name])
            if not ok:
                # oops, too long, __prep... already responded to 
                # user, so we'll just return
                return True

            rsp= _st(msg.sender, "direct-blast-acknowledge %(text)s %(recipient)s") % \
                {'recipient':name,'text':out_text}
 
            self.debug('REPSONSE TO BLASTER: %s' % rsp)
            self.__reply(msg,rsp)

            if isinstance(obj, Village):
                self.__blast_to_villages([obj],msg.sender,out_text)
            else:
                assert(isinstance(obj, Contact))
                self.__blast_to_contact(obj,out_text)
        return True

    def blast(self, msg):
        """Takes actual Contact objects"""
        self.debug("SMSFORUM:BLAST")

        #find all villages for this sender
        villes = villages_for_contact(msg.sender)
        if len(villes)==0:
            rsp=_st(msg.sender, "blast-fail_not-member-of-any-village")
            self.debug(rsp)
            self.__reply(msg,rsp)
            return True

        recips=[v.name for v in villes]
        ok,blast_text,enc=self.__prep_blast_message(msg,msg.text,recips)
        if not ok:
            # message was too long, prep already
            # sent a reply to the sender, so we just 
            # return out
            return True

        # respond to sender first because the delay between now 
        # and the last recipient can be long
        #
        # TODO: send a follow-up is message sending fails!
        rsp= _st(msg.sender, "blast-acknowledge %(text)s %(recipients)s") % \
            {'recipients':', '.join(recips),'text':msg.text.strip()} 
        self.debug('REPSONSE TO BLASTER: %s' % rsp)
        self.__reply(msg,rsp)

        return self.__blast_to_villages(villes,msg.sender,blast_text)
    
    def __prep_blast_message(self,msg,out_text,recipients):
        """
        helper function formats blast msg
        including signature and returns 3-ple
        of ( bool <message is good to send>, 
        formatted message w/signature, encoding required)
        
        If message is NOT good to send 3-ple will be
        (False, None, encoding)

        NOTE: If the message is too long this helper
        sends a reply to the msg.sender, so don't do
        that again!
        
        """

        # check for message length, and bounce messages that are too long
        #
        # since length depends on encoding, find out if we can send 
        # this GSM (160 chars) or UCS2 (70 chars)
        #
        # TODO: factor this somewhere better like the backend since
        # it's what knows the message size limits...
        #

        gsm_enc=True
        sender_sig=msg.sender.signature
        try:
            out_text.encode('gsm')
            sender_sig.encode('gsm')
        except:
            # Either message or sig needs UCS2 encoding
            gsm_enc=False
        finally:
            encoding,max_len=(\
                ('gsm',MAX_LATIN_BLAST_LEN) if gsm_enc \
                    else ('ucs2',MAX_UCS2_BLAST_LEN))
            
        if len(out_text)>max_len: 
            rsp= _st(msg.sender, "blast-fail_message-too-long %(msg_len)d %(max_latin)d %(max_unicode)d") % \
                {
                'msg_len': len(out_text),
                'max_latin': MAX_LATIN_BLAST_LEN,
                'max_unicode': MAX_UCS2_BLAST_LEN
                } 
            self.__reply(msg,rsp)
            return (False, None, encoding)

        # ok, we're long enough, lets make the blast text
        # we replace '%(sender)s' with '%(sender)s' so that
        # localized strings can put the sender where they want
        # we then do another subsitution after we pick the send signature
        blast_tmpl=_st(msg.sender, "blast-message_outgoing %(text)s %(recipients)s %(sender)s") % \
            { 'text':out_text, 'recipients':', '.join(recipients), 'sender': '%(sender)s'}

        #add signature
        tmpl_len=len(blast_tmpl)-10  # -10 accounts from sig placeholder ('%(sender)s')
        max_sig=max_len-tmpl_len
        sig=msg.sender.get_signature(max_len=max_sig,for_message=msg)
        blast_text = blast_tmpl % {'sender': sig}
        return (True, blast_text, encoding)

    def __blast_to_villages(self, villes, sender, text):
        """Takes actual village objects"""
        if villes is None or len(villes)==0:
            return True

        recipients=set()
        for ville in villes:
            recipients.update(ville.flatten(klass=Contact))
            
        # now iterate every member of the group we are broadcasting
        # to, and queue up the same message to each of them
        for recipient in recipients:
            if recipient != sender:
                self.__blast_to_contact(recipient,text)
        vnames = ', '.join([v.name for v in villes])
        self.debug("success! %(villes)s recvd msg: %(txt)s" % { 'villes':vnames,'txt':text})
        return True

    def __blast_to_contact(self, contact, text):
        """Returns True is message sent"""
        if contact.can_receive:
            self.debug('Blast msg: %s to: %s' % (text,contact.signature))
            # TODO: move to lib/pygsm/gsm.py
            # currently just log messages that are too long
            # since these are not handled properly in modem
            self._check_message_length(text)
            contact.send_to(text)
            return True
        else:
            return False

    def leave(self,msg,arg=None):
        self.debug("SMSFORUM:LEAVE: %s" % arg)
        try:
            villages=[]
            if arg is not None and len(arg)>0:
                village_tupes = self.village_matcher.match(arg, with_data=True)
                if len(village_tupes)>0:
                    villages = zip(*village_tupes)[1] # the objects
            else:
                villages = villages_for_contact(msg.sender)
            if len(villages)>0:
                names = list()
                for ville in villages:
                    msg.sender.remove_from_parent(ville)
                    names.append(ville.name)
                self.__reply(msg, "leave-success %(villages)s",
                             { "villages": ','.join(names)})
            else:
                if arg is not None and len(arg)>0:
                    self.__reply(msg, "leave-fail_village-not-found %(village)s", {'village':arg})
                else:
                    self.__reply(msg, "leave-fail_not-member-of-village")
        except:
            # something went wrong - at the
            # moment, we don't care what
            traceback.print_exc()
            self.debug( traceback.format_exc() )
            self.__reply(msg, "internal-error")

        return True

    def lang(self,msg,arg=None):
        name=arg
        self.debug("SMSFORUM:LANG:Current locale: %s" % msg.sender.locale)
        
        def _return_all_langs():
            # return available langs
            langs_sorted=_G['SUPPORTED_LANGS'].values()
            langs_sorted.sort()
            rsp=_st(msg.sender, "language-set-fail_code-not-understood %(langs)s") % \
                { 'langs':', '.join(langs_sorted)}
            self.__reply(msg,rsp)
            return True

        if name is None or len(name)==0:
            return _return_all_langs()
        
        # see if we have that language
        langs=self.lang_matcher.match(name.strip(),with_data=True)
        if len(langs)==1:
            name,code=langs[0]
            msg.sender.locale=code
            msg.sender.save()
            rsp = _st(msg.sender, 'language-set-success %(lang)s') % { 'lang': name }
            self.__reply(msg,rsp)
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
        reply_text=_st(msg.sender,reply_text) 
        if format_values is not None:
            try:
                reply_text = reply_text % format_values
            except TypeError:
                err="Not all format values: %r were used in the string: %s" %\
                    (format_values, reply_text)
                self.error(err)
        # TODO: move to lib/pygsm/gsm.py
        # currently just log messages that are too long
        # since these are not handled properly in modem
        self._check_message_length(reply_text)
        msg.sender.send_response_to(reply_text)
    
    def __suggest_villages(self,msg):
        """helper to send informative messages"""
        # pick some names from the DB
        village_names = [v.name for v in Village.objects.all()[:3]]
        if len(village_names) == 0:
            village_names = _st(msg.sender,"village_name")
        else: 
            village_names=', '.join(village_names)
        self.__reply(msg,"village-not-found %(suggested)s", {"suggested": village_names})
        return True

    def __loadFixtures(self):
        pass

    def __log_incoming_message(self,msg,domains):
        #TODO: FIX THIS so that it logs for all domains
        if domains is None or len(domains)==0:
            return

        #msg.persistent_msg should never be none if app.logger is used
        #this is to ensure smsforum does not fail even if logger fails...
        if msg.persistent_msg is not None:
            msg.persistent_msg.domain = domains[0]
            msg.persistent_msg.save()

    def _check_message_length(self, text):
        """
        This function DOES NOT belong here - a temporary measure until 
        rapidsms has a good api for backends to speak to router
        
        checks message length < 160 if gsm, else <70 if ucs-2/utf16
        """

        gsm_enc=True
        try:
            text.encode('gsm')
        except:
            gsm_enc=False
        finally:
            encoding,max_len=(\
                ('gsm',MAX_LATIN_SMS_LEN) if gsm_enc \
                    else ('ucs2',MAX_UCS2_SMS_LEN))
        
        if len(text)>max_len:
            err= ("ERROR: %(encoding)s MESSAGE OF LENGTH '%(msg_len)d' IS TOO LONG. Max is %(max)d.") % \
                         {
                'encoding': encoding,
                'msg_len': len(text),
                'max': MAX_LATIN_SMS_LEN if encoding=='gsm' else MAX_UCS2_SMS_LEN
                } 
            self.error(err)
            return False
        return True

