#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from rapidsms.tests.scripted import TestScript
import apps.smsforum.app as smsforum_app
import apps.smsforum.app as smsforum_app
import apps.logger.app as logger_app
import apps.contacts.app as contacts_app
from app import App
from django.core.management.commands.dumpdata import Command
import time
import random
import os
from datetime import datetime
 
class TestApp (TestScript):
    apps = (smsforum_app.App, contacts_app.App, logger_app.App, App )

    def setUp(self):
        TestScript.setUp(self)
        #should setup default village in here
        
    testJoinAndBlast = """
        8005551210 > .create village
        8005551210 < Community 'village' was created
        8005551210 > .join village
        8005551210 < Thank you for joining the village community - welcome!
        8005551210 > message to blast
        8005551210 < Your message was sent to these communities: village
        """
    
    testGroupBlast = """
        8005551212 > .create village2
        8005551212 < Community 'village2' was created
        8005551212 > .join village2
        8005551212 < Thank you for joining the village2 community - welcome!
        8005551213 > .join village2
        8005551213 < Thank you for joining the village2 community - welcome!
        8005551212 > msg_to_blast
        8005551212 < Your message was sent to these communities: village2
        8005551213 < msg_to_blast - 8005551212
        8005551212 > .leave
        8005551212 < You have left these communities: village2
        """
    
    testMegaGroupBlast = """
        8005551215 > .create village3
        8005551215 < Community 'village3' was created
        8005551215 > .join village3
        8005551215 < Thank you for joining the village3 community - welcome!
        8005551216 > .join village3
        8005551216 < Thank you for joining the village3 community - welcome!
        8005551217 > .join village3
        8005551217 < Thank you for joining the village3 community - welcome!
        8005551218 > .join village3
        8005551218 < Thank you for joining the village3 community - welcome!
        8005551219 > .join village3
        8005551219 < Thank you for joining the village3 community - welcome!
        8005551215 > msg_to_blast
        8005551215 < Your message was sent to these communities: village3
        8005551216 < msg_to_blast - 8005551215
        8005551217 < msg_to_blast - 8005551215
        8005551218 < msg_to_blast - 8005551215
        8005551219 < msg_to_blast - 8005551215
        8005551215 > .leave
        8005551215 < You have left these communities: village3
        """
        
    testLang = """
        8005551212 > .lang eng
        8005551212 < You language has been set to: English
        8005551212 > .lang fra
        8005551212 < La langue que vous avez sélectionnée est 'Français'
        8005551212 > .lang wol
        8005551212 < Làkk wi nga tànn moo kàllaama Wolof
        8005551212 > .lang joo
        8005551212 < kasankenak kanu fajulumi ku 'Joola'
        8005551212 > .lang pul
        8005551212 < Åemngal ngal cuøi- daa ko Pulaar.
        """
    
    testAllCommandsEnglish = """
        8005551220 > .create village4
        8005551220 < Community 'village4' was created
        8005551220 > .join village4
        8005551220 < Thank you for joining the village4 community - welcome!
        8005551220 > message to blast
        8005551220 < Your message was sent to these communities: village4
        8005551220 > .name foo
        8005551220 < Hello foo!
        8005551220 > .member
        8005551220 < You are a member of these communities: village4
        8005551220 > .citizens village4
        8005551220 < village4: 8005551220
        8005551220 > .leave village4
        8005551220 < You have left these communities: village4
        8005551220 > .remove village4
        8005551220 < The community 'village4' was removed.
        8005551220 > .language eng
        8005551220 < You language has been set to: English
        8005551220 > .help
        8005551220 < Available Commands: #join COMMUNITY - #leave - #name NAME - #lang LANG
        """
        
    testAllCommandsFrench = u"""
        8005551220 > .créer village5
        8005551220 < La communauté village5 a été créée
        8005551220 > .créer village6
        8005551220 < La communauté village6 a été créée
        8005551220 > .entrer village6
        8005551220 < Merci d'avoir rejoint la communauté 'village6' - bienvenue!
        8005551220 > message to blast
        8005551220 < Votre message a été envoyé à: village6
        8005551220 > .nom foo
        8005551220 < Bonjour foo. Merci d'avoir enregistré votre nom! Il apparaitra dorénavant sur tous les messages que vous envoyez
        8005551220 > .quitter village6
        8005551220 < Vous venez de quitter la communauté 'village6' Au revoir!
        8005551220 > .language fra
        8005551220 < La langue que vous avez sélectionnée est 'Français'
        8005551220 > .aide
        8005551220 < Vous pouvez texter: #entrer COMMUNAUTE - #quitter - #nom NOM - #lang LANG
        """
         
    testAllCommandsWolof = u"""
        8005551220 > .lang wol
        8005551220 < Làkk wi nga tànn moo kàllaama Wolof
        8005551220 > .créer village7
        8005551220 < Dekk bi, ci village7 lañu ko sos
        8005551220 > .duggu village7
        8005551220 < Jerejef ci dugg bi nga dugg ci 'village7 ' dalal ak jamm
        8005551220 > .tur mon nom
        8005551220 < Jàmm ngaam mon nom: Jerejef ci li nga dugal sa tur ! gannaawsi tey, tur woowu mooy feeñ ci bépp xebaar boo yonnee.
        8005551220 > message to blast
        8005551220 < yonnee ko ci village7
        8005551220 > .génn village7
        8005551220 < Joge nga ci dekk bi 'village7' Ba beneen.
        8005551220 > .genn village7
        8005551220 < Joge nga ci dekk bi 'village7' Ba beneen.
        8005551220 > .ndimbal
        8005551220 < Buton yi jàppandi: #duggu TURU DEKK BI - #genn - #tur SA TUR - #help-wol
        """
                
    testAllCommandsPulaar = u"""
        8005551220 > .lang pul
        8005551220 < Åemngal ngal cuøi- daa ko Pulaar.
        8005551220 > .créer village8
        8005551220 < Sahre nåe sinicaa ko village8
        8005551220 > .naalde village8
        8005551220 < a Jaaraama nåe tawtu - åaa e Sahre nåe 'village8' - Bisimilla!
        8005551220 > .tawtude village8
        8005551220 < a Jaaraama nåe tawtu - åaa e Sahre nåe 'village8' - Bisimilla!
        8005551220 > .yettoode foo
        8005551220 < Jam waali foo. A jaaraama nåe møinndu - åaa innåe. Maa feeñoy e kala nåe  nulåu-åon kaøaaruuji.
        8005551220 > message to blast
        8005551220 < nulåu feewåe e 'village8'
        8005551220 > .yaltude village8
        8005551220 < On ngiwii to sahre to 'village8' haa nalnde woånde
        8005551220 > .dallal
        8005551220 < Vous pouvez texter: #naalde VILLAGE - #yaltude - #yettoode NAME - #help-pul
        """
        
    testAllCommandsJoola = u"""
        8005551220 > .lang joo
        8005551220 < kasankenak kanu fajulumi ku 'Joola'
        8005551220 > .créer village9
        8005551220 < fujojaf fati village9 futuukituuk
        8005551220 > .unoken village9
        8005551220 < abaraka manunoken na di fujojaf fati 'village9'
        8005551220 > message to blast
        8005551220 < e messagey yanou bogn mi di fou jojaf e rin-ding 'village9'
        8005551220 > .karees foo
        8005551220 < Saafuul, foo.abaraka manunokene kareesi.naa,naapuciikumi panimanj aima. Abaraka.
        8005551220 > .upur village9
        8005551220 < nupupur di fujojaf fati village9. be nikeen!
        8005551220 > .rambenom
        8005551220 < Uciik #unoken karees kati esukey _ #upur _ #karees _ #rambenom
        """

    testErrorCodes = """
        8005551216 > .join
        8005551216 < Sorry, I don't know that place. Did you mean one of: community name ?
        8005551215 > .leave village
        8005551215 < Could not find a community named 'village'
        8005551216 > .join village
        8005551216 < Sorry, I don't know that place. Did you mean one of: community name ?
        8005551216 > .lang
        8005551216 < You may set your language to any of: English, Français, Joola, Pulaar, Wolof
        8005551216 > .create
        8005551216 < Please send a village name, e.g. #create 'community name'
        8005551216 > .member village
        8005551216 < You are not a member of any community
        8005551215 > .leave
        8005551215 < You are not a member of any communities
        8005551216 > .create village
        8005551216 < Community 'village' was created
        8005551216 > .join village
        8005551216 < Thank you for joining the village community - welcome!
        8005551216 > msg_to_blast_longer_than_160_msg_to_blast_longer_than_160_msg_to_blast_longer_than_160_msg_to_blast_longer_than_160_msg_to_blast_longer_than_160_msg_to_blast_longer_than_160
        8005551216 < Message length (173) is too long. Latin script max: 140. Unicode max: 60
        """
    
    testFunnyCharacters = u"""
        8005551216 > .help èoâoé
        8005551216 < Available Commands: #join COMMUNITY - #leave - #name NAME - #lang LANG
        8005551216 > .create èoâoé
        8005551216 < Community 'èoâoé' was created
        8005551216 > .join èoâoé
        8005551216 < Thank you for joining the èoâoé community - welcome!
        8005551216 > .name èoâoé
        8005551216 < Hello èoâoé!
        8005551216 > blast èoâoé
        8005551216 < Your message was sent to these communities: èoâoé
        8005551216 > .leave èoâoé
        8005551216 < You have left these communities: èoâoé
        8005551216 > .language èoâoé
        8005551216 < You may set your language to any of: English, Français, Joola, Pulaar, Wolof
        8005551216 > .member èoâoé
        8005551216 < You are not a member of any community
        8005551216 > .citizens èoâoé
        8005551216 < èoâoé: 
        8005551216 > .remove èoâoé
        8005551216 < The community 'èoâoé' was removed.
        """
