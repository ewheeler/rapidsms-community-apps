#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

class KeywordActions():
    ''' Methods in this class will be called whenever the keyword
        is matched in a message (after any forms have been parsed).
        Methods should have the same name as the keyword plus either
        _silent or _responding (corresponding with Action type choices).
        'silent' functions are executed silently -- nothing is done with
        anything they return. Anything returned by a 'responding' function
        will be sent as a response to the message that contained the keyword. '''

    @staticmethod
    def beta_silent():
        print 'explosion!!!'
        return "BANG"

    @staticmethod
    def gamma_responding():
        return "short-circuit!!"

class FormActions():
    ''' Methods in this class will be called after a keyword's form
        has been parsed. Methods should have the same name as the keyword. '''

    @staticmethod
    def alpha(formentry, errors):
        print "HARDCORE FORM ACTION"
