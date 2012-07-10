# -*- coding: utf-8 -*-

# Focus
# Copyright (C) 2010-2012 Grid Dynamics Consulting Services, Inc
# All Rights Reserved
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program. If not, see
# <http://www.gnu.org/licenses/>.


import os

import flask


class SessionData(dict, flask.sessions.SessionMixin):
    pass


class Session(flask.sessions.SessionInterface):
    session_class = SessionData

    def open_session(self, app, request):
        self.cookie_session_id = request.cookies.get(
            app.session_cookie_name, None)
        self.session_new = False
        if self.cookie_session_id is None:
            self.cookie_session_id = os.urandom(40).encode('hex')
            self.session_new = True
        self.memcache_session_id = '@'.join(
            [
                request.remote_addr,
                self.cookie_session_id
            ]
        )
        session = app.cache.get(self.memcache_session_id) or {}
        app.cache.set(self.memcache_session_id, session)
        return self.session_class(session)

    def save_session(self, app, session, response):
        expires = self.get_expiration_time(app, session)
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)
        app.cache.set(self.memcache_session_id, session)
        if self.session_new:
            response.set_cookie(
                app.session_cookie_name, self.cookie_session_id, path=path,
                expires=expires, httponly=httponly,
                secure=secure, domain=domain)
