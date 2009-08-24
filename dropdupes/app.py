#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import hashlib
import rapidsms


class App(rapidsms.app.App):

    def start(self):
        self.msg_log = []

    def configure(self, max_log_size=20):
        self.max_log_size = max_log_size

    def filter(self, message):

        # hash this message, to identify it uniquely without
        # storing the message itself. it _should_ be possible
        # to include the date that the message was sent in this,
        # to (much) further improve the accurancy, but not all
        # backends set it correctly at the moment.
        msg_hash = hashlib.sha1(
            "%s|%s|%s" % (
                message.connection.backend.slug,
                message.connection.identity,
                message.text)
        ).hexdigest()

        self.info("Message hash: %s", msg_hash)
        
        # if we've already seen this message,
        # then return True to stop processing
        if msg_hash in self.msg_log:
            self.warning(
                "Dropped duplicate delivery: %r",
                msg_hash)
            return True

        # add the new message hash to the log
        self.msg_log.append(msg_hash)
        
        # if the log is too long, forget the oldest message,
        # to ensure that we're not dropping messages based
        # on things that arrived ages ago
        if len(self.msg_log) > self.max_log_size:
            self.msg_log.pop(0)

        # this message isn't a dupe, so instruct
        # the router to continue processing it
        return None
