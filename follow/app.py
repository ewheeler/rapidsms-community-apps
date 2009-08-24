#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import re
from utils import followable_models
import rapidsms


class App(rapidsms.app.App):
    """This app provides a generic way for Reporters and PersistantConnections
       to "follow" events triggered by other models. Any model that implements
       the __search__ method can be followed."""

    FOLLOW_RE   = re.compile(r"^(?:follow|watch)\s*(.+)$", re.I)
    UNFOLLOW_RE = re.compile(r"^un(?:follow|watch)\s*(.+)$", re.I)
    SPLIT_RE    = re.compile(r"[\s,]+", re.I)


    def _slice(self, str):
        return self.SPLIT_RE.split(str)


    def _dice(self, x):
        """Returns the elements of iterable _x_ in tuples of every possible
           length and range, without changing the order. This is useful when
           parsing a list of undelimited terms, which may span multiple tokens.
           For example (note the decreasing length of the tuples):
           >>> _dice(["a", "b", "c"])
           [("a", "b", "c"),  ("a", "b"), ("b", "c"),  ("a"), ("b"), ("c")]"""

        y = []
        for n in range(len(x), 0, -1):
            for m in range(0, len(x)-(n-1)):
                y.append(tuple(x[m:m+n]))

        return y


    def handle(self, msg):

        # is this a follow request?
        # > FOLLOW @123456
        # > FOLLOW adam, evan
        # > FOLLOW chipoka chikuse wat
        match = self.FOLLOW_RE.match(msg.text)
        if match is not None:
            terms = match.group(1)
            to_follow = []

            # since the terms are undelimited, we'll have to figure out what
            # the sender means by brute force. smash the terms string into all
            # of it's possible combinations, and pass every one to every model
            # that implements the __search__ API to see if it's recognized
            combinations = self._dice(self._slice(terms))
            for combo in combinations:
                for model in followable_models():
                    obj = model.__search__(None, combo)
                    if obj is not None:

                        # we found a match! take note, and
                        # skip to the next combination
                        self.info(
                            '%r parsed into "%r" by %r' %
                            (combo, obj, model))
                        to_follow.append(obj)
                        break

            # add this reporter (or connection) to
            # the "followers" reverse foreign key
            for obj in to_follow:
                obj.followers.get_or_create(**msg.persistance_dict)

            msg.respond(
                u"You are now following: %s" %
                (", ".join(map(unicode, to_follow))))

            return True

        # is this an unfollow request?
        pass

        # is this a "who am i following?" request?
        pass
