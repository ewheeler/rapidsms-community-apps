#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import rapidsms


class App(rapidsms.app.App):
    _slug = "backends"
    
    def ajax_GET_status(self, params):
        return dict([
            (be.slug, be.status())
            for be in self.router.backends
            if hasattr(be, "status") ])
