#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

import re, os
import rapidsms
from rapidsms.parsers import Matcher
from rapidsms.message import Message
from rapidsms.parsers.bestmatch import BestMatch
from models import *
from apps.locations.models import *
import gettext
import traceback
import string

from apps.smsforum.models import *
from apps.contacts.models import *

DEFAULT_VILLAGE="Keur Samba Laube"
DEFAULT_LANGUAGE="fre"
MAX_BLAST_CHARS=130
CMD_MESSAGE_MATCHER=re.compile(ur'^\s*([\.\*\#])\s*(\S+)?\s*',re.IGNORECASE)

class App(rapidsms.app.App):
    # tuple of 'name,language_code'
    SUPPORTED_LANGUAGES = [
        (u'English', 'eng'),
        (u'Français', 'fre'),
        (u'Pulaar','pul'),
        (u'Wolof', 'wol'),
        (u'Debug', 'deb')
        ]

    def help(self, msg,args):
        # TODO: grab senders language and translate based on that
        msg.respond( _("help with commands") )

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
            ('lang', {'lang':'eng','func':self.lang}),
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
        self.lang_matcher=BestMatch(self.SUPPORTED_LANGUAGES)
        print self.lang_matcher.targets

    def start(self):
        # since the functionality of this app depends on a default group
        # make sure that this group is created explicitly in this app 
        # (instead of depending on a fixture)
        self.__loadFixtures()
        self.__initTranslators()
        
        # fetch a list of all the backends
        # that we already have objects for
        known_backends = CommunicationChannel.objects.values_list("slug", flat=True)
        
        # find any running backends which currently
        # don't have objects, and fill in the gaps
        for be in self.router.backends:
            if not be.slug in known_backends:
                self.info("Creating PersistantBackenD object for %s (%s)" % (be.slug, be.title))
                CommunicationChannel(slug=be.slug, title=be.title).save()    
    
    def parse(self, msg):
        self.debug("REPORTER:PARSE")
        # fetch the persistantconnection object
        # for this message's sender (or create
        # one if this is the first time we've
        # seen the sender), and stuff the meta-
        # dta into the message for other apps
        msg.persistent_channel= CommunicationChannelFromMessage(msg)
        msg.persistant_connection = ChannelConnectionFromMessage(msg)
        msg.sender = ContactFromMessage(msg)
        
        # store a handy dictionary, containing the most useful persistance
        # information that we have. this is useful when creating an object
        # linked to _something_, like so:
        # 
        #   class SomeObject(models.Model):
        #     reporter   = models.ForeignKey(Reporter, null=True)
        #     connection = models.ForeignKey(PersistantConnection, null=True)
        #     stuff      = models.CharField()
        #
        #   # this object will be linked to a reporter,
        #   # if one exists - otherwise, a connection
        #   SomeObject(stuff="hello", **msg.persistance_dict)
        if msg.sender: msg.persistance_dict = { "reporter": msg.sender }
        else:            msg.persistance_dict = { "connection": msg.persistant_connection }
        
        # log, whether we know who the sender is or not
        if msg.sender: self.info("Identified: %s as %r" % (msg.persistant_connection.user_identifier, msg.sender))
        else:            self.info("Unidentified: %s" % (msg.persistant_connection.user_identifier))
    
    def handle(self, msg):
        self.debug("REPORTER:HANDLE: %s" % msg.text)
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
            msg.respond(_("Je comprends pas cet ordre"))
            return True

        # Now match the possible command to ones we know
        cmd_match=self.cmd_matcher.match(cmd,with_data=True)

        if len(cmd_match)==0:
            # no command match
            msg.respond(_("Je comprends pas cet ordre"))
            return True

        if len(cmd_match)>1:
            # too many matches!
            msg.respond(_('Command not understood. Did you mean one of: %(firsts)s or %(last)s?' %\
                              { 'firsts':', '.join([t[0] for t in cmd_match[:-1]]),
                                'last':cmd_match[-1:][0][0]}))
            return True

        # Ok! We got a real command
        
        # strip command from the
        args=msg_text[msg_match.end():]
        print cmd_match
        return cmd_match[0][1]['func'](msg,args)
        
      
    # admin utility!
    def createvillage(self, msg, village=DEFAULT_VILLAGE):
        village = village.strip()

        try:
            # TODO: add administrator authentication
            self.debug("REPORTER:CREATEVILLAGE")
            ville = Village.objects.get_or_create(name=village)
            self.village_matcher.add_target(village)
            msg.respond( _("village %s created") % (village) )
            # TODO: remove this for production
        except:
            traceback.print_exc()
            msg.respond(
                _("register-fail") 
                )

        return True
             
    def register_name(self, msg, family_name):
        try:
            msg.sender.family_name = family_name
            msg.sender.save()
            rsp=( _("name-register-success %(name)s") % {'name':family_name} )
            msg.respond(rsp)
        except:
            traceback.print_exc()
            rsp= _("register-fail")
            self.debug(rsp)
            msg.respond(rsp)

        return True

    def join(self, msg, village):
        try:
            matched_villes=self.village_matcher.match(village)
            # send helpful message if 0 or more than 1 found
            num_villes=len(matched_villes)
            if num_villes==0 or num_villes>1:
                if num_villes==0:
                    # pick some names from the DB
                    all_villages = Village.objects.all()[:3]
                    village_names = ""
                    if len(all_villages) == 0:
                        village_names = "village name"
                    else: 
                        village_names=', '.join(village_names)
                else:
                    # use all hit targets
                    village_names=', '.join(matched_villes)
                resp =  _("village does not exist") % {"village_names": village_names} 
                msg.respond(resp)
                return True

            # ok, here we got just one
            rs=Village.objects.filter(name=matched_villes[0])
            if len(rs) != 1:
                # huh? that's supposed to be Unique
                raise Exception('Multiple entries for village: %s' % matched_villes[0])

            ville=rs[0]
            msg.sender.add_to_group(ville)
            rsp=_("first-login") % {"village": ville.name } 
            self.debug(rsp)
            msg.respond(rsp)
        except:
            traceback.print_exc()
            rsp=_("register-fail")
            self.debug(rsp)
            msg.respond(rsp)

        return True
            
    def blast(self, msg):
        txt = msg.text
        try:
            sender = msg.sender

            # check for message length, and bounce messages that are too long
            if len(txt) > MAX_BLAST_CHARS:
                rsp= _("Message was not delivered. Please send less than %(max_chars)d characters.") % {'max_chars': MAX_BLAST_CHARS} 
                msg.respond(rsp)
                return True

            #if sender is None:
            #    #join default village and send to default village
            #    sender = self.join(msg)

            self.debug("REPORTER:BLAST")
            #find all reporters from the same location
            villages = VillagesForContact(sender)
            if len(villages)==0:
                rsp=_("You must join a village before sending messages")
                self.debug(rsp)
                msg.respond(rsp)
                return True
            village_names = ''
            for ville in villages:
                village_names = ("%s %s") % (village_names, ville.name) 
            rsp= _("success! %(villes)s recvd msg: %(txt)s") % {'villes':village_names,'txt':txt} 
            self.debug('REPSONSE TO BLASTER: %s' % rsp)
            msg.respond(rsp)
            recipients=set()
            for ville in villages:
                recipients.update(ville.flatten())

            # because the group can be _long_ and messages are delivered
            # serially on a single modem install, it can take a long time
            # (minutes, 10s of minutes) to send all.
            # SO to keep people from thinking it didn't work and resending, 
            # send there response first
            rsp_template=string.Template(_("%(txt)s - sent to [%(ville)s] from %(sender)s") % \
                { 'txt':txt, 'ville':ville.name, 'sender':'$sig'})
            # now iterate every member of the group we are broadcasting
            # to, and queue up the same message to each of them
            for recipient in recipients:
                if int(recipient.id) != int(sender.id):
                    #add signature
                    announcement = rsp_template.substitute(sig=sender.signature().replace('$','$$'))
                    #todo: limit chars to 1 txt message?
                    conns = ChannelConnection.objects.all().filter(contact=recipient)
                    for conn in conns:
                        # todo: what is BE is gone? Use different one?
                        self.debug( "SENDING ANNOUNCEMENT TO: %s VIA: %s" % (conn.user_identifier,conn.communication_channel.slug))
                        be = self.router.get_backend(conn.communication_channel.slug)
                        be.message(conn.user_identifier, announcement).send()

            village_names = village_names.strip()
            self.debug( _("success! %(villes)s recvd msg: %(txt)s") % { 'villes':village_names,'txt':txt})
            return True
        except:
            traceback.print_exc()
            msg.respond(
                _("blast-fail") 
            )
        
        return True

    def leave(self, msg,arg):
        try:
            self.debug("REPORTER:LEAVE")
            if msg.sender is not None:
                villages=VillagesForContact(msg.sender)
                if len(villages)>0:
                    #default to deleting all persistent connections with the same identity
                    #we can always come back later and make sure we are deleting the right backend
                    names=list()
                    for ville in villages:
                        msg.sender.remove_from_group(ville)
                        names.append(ville.name)
                    msg.respond(
                        _("leave-success") % { "village": ','.join(names)})
                    return True
            msg.respond( _("nothing to leave") )
            return True
        # something went wrong - at the
        # moment, we don't care what
        except:
            traceback.print_exc()
            msg.respond(
                _("leave-fail") 
            )

        return True

    def lang(self, msg, name):
        # TODO: make this a decorator to be used in all functions
        # so that users don't have to register in order to get going
        self.debug("REPORTER:LANG")
        
        # see if we have that language
        langs=self.lang_matcher.match(name.strip(),with_data=True)
        if len(langs)==1:
            name,code=langs[0]
            msg.sender.set_locale(code)
            msg.sender.save()
            self.__setLocale(code)
            resp = _("lang-set %(lang_code)s") % { 'lang_code': name }
            self.debug(resp)
        
        # invalid language code. don't do
        # anything, just send an error message
        else: 
            resp = _("bad-lang")
        
        msg.respond( resp )
        return True
    
    def __loadFixtures(self):
        # Village.objects.get_or_create(name=DEFAULT_VILLAGE)
        pass
         
    def __initTranslators(self):
        self.translators = {}
        path = os.path.join(os.path.dirname(__file__),"locale")
        for name,lang in self.SUPPORTED_LANGUAGES:
            trans = gettext.translation(lang,path,[lang])
            self.translators.update( {lang:trans} )
        self.__setLocale(DEFAULT_LANGUAGE)

    def __setLocale(self, locale):
        if locale is not None:
            self.translators[locale].install(unicode=1)
        else: 
            self.__setLocale(DEFAULT_LANGUAGE)


    

