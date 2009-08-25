#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import re
import rapidsms
from rapidsms.search import find_objects
import utils


class App(rapidsms.app.App):
    """This app provides a generic way for Reporters and PersistantConnections
       to "follow" events triggered by other models. Any model that implements
       the __search__ method can be followed."""

    FOLLOW_RE   = re.compile(r"^(?:follow|watch)\s*(.+)$", re.I)
    UNFOLLOW_RE = re.compile(r"^un(?:follow|watch)\s*(.+)$", re.I)


    def handle(self, msg):

        # is this a follow request?
        # > FOLLOW @123456
        # > FOLLOW adam, evan
        # > FOLLOW chipoka chikuse wat
        match = self.FOLLOW_RE.match(msg.text)
        if match is not None:
            models = utils.followable_models()
            to_follow = find_objects(models, match.group(1))

                # we found a match! take note, and
                # skip to the next combination
                #self.info(
                #    '%r parsed into "%r" by %r' %
                #    (combo, obj, model))
                #        #break

            # add each reporter (or connection) to
            # the "followers" reverse foreign key
            for obj in to_follow:
                obj.followers.get_or_create(**msg.persistance_dict)

            if to_follow:
                msg.respond(
                    u"You are now following: %s" %
                    (", ".join(map(unicode, to_follow))))

            return True

        # is this an unfollow request?
        pass

        # is this a "who am i following?" request?
        pass
