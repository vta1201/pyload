# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: mkaay, RaNaN
"""

try:
    from json import loads
except ImportError:
    from simplejson import loads

from thread import start_new_thread
from pycurl import FORM_FILE

from module.network.RequestFactory import getURL

from module.plugins.Hook import Hook

PYLOAD_KEY = "9f65e7f381c3af2b076ea680ae96b0b7"

class CaptchaTraderException(Exception):
    def __init__(self, err):
        self.err = err

    def getCode(self):
        return self.err

    def __str__(self):
        return "<CaptchaTraderException %s>" % self.err

    def __repr__(self):
        return "<CaptchaTraderException %s>" % self.err

class CaptchaTrader(Hook):
    __name__ = "CaptchaTrader"
    __version__ = "0.1"
    __description__ = """send captchas to captchatrader.com"""
    __config__ = [("activated", "bool", "Activated", True),
                  ("username", "str", "Username", ""),
                  ("force", "bool", "Force CT even if client is connected", False),
                  ("passkey", "password", "Password", ""),]
    __author_name__ = ("RaNaN")
    __author_mail__ = ("RaNaN@pyload.org")

    SUBMIT_URL = "http://captchatrader.com/api/submit"
    RESPOND_URL = "http://captchatrader.com/api/respond"
    GETCREDITS_URL = "http://captchatrader.com/api/get_credits/username:%(user)s/password:%(password)s/"


    def getCredits(self):
        json = getURL(CaptchaTrader.GETCREDITS_URL % {"user": self.getConfig("username"),
                                                           "password": self.getConfig("passkey")})
        response = loads(json)
        if response[0] < 0:
            raise CaptchaTraderException(response[1])
        else:
            self.log.debug("CaptchaTrader: %s credits left" % response[1])
            return response[1]

    def submit(self, captcha, captchaType="file", match=None):
        if not PYLOAD_KEY:
            raise CaptchaTraderException("No API Key Specified!")

        #if type(captcha) == str and captchaType == "file":
        #    raise CaptchaTraderException("Invalid Type")
        assert captchaType in ("file", "url-jpg", "url-jpeg", "url-png", "url-bmp")
        json = getURL(CaptchaTrader.SUBMIT_URL, post={"api_key": PYLOAD_KEY,
                                                           "username": self.getConfig("username"),
                                                           "password": self.getConfig("passkey"),
                                                           "value": (FORM_FILE, captcha),
                                                           "type": captchaType}, multipart=True)
        response = loads(json)
        if response[0] < 0:
            raise CaptchaTraderException(response[1])

        ticket = response[0]
        result = response[1]
        self.log.debug("CaptchaTrader result %s : %s" % (ticket,result))

        return ticket, result

    def respond(self, ticket, success):
        json = getURL(CaptchaTrader.RESPOND_URL, post={"is_correct": 1 if success else 0,
                                                            "username": self.getConfig("username"),
                                                            "password": self.getConfig("passkey"),
                                                            "ticket": ticket})
        response = loads(json)
        if response[0] < 0:
            raise CaptchaTraderException(response[1])

    def newCaptchaTask(self, task):
        if not self.getConfig("username") or not self.getConfig("passkey"):
            return False

        if not (self.core.isClientConnected() and self.getConfig("force")):
            return False

        if self.getCredits() > 10:
            task.handler.append(self)
            task.setWaiting(40)
            start_new_thread(self.processCaptcha, (task,))

        else:
            self.log.info(_("Your CaptchaTrader Account has not enough credits"))

    def captchaCorrect(self, task):
        if task.data.has_key("ticket"):
            ticket = task.data["ticket"]
            self.respond(ticket, True)

    def captchaWrong(self, task):
        if task.data.has_key("ticket"):
            ticket = task.data["ticket"]
            self.respond(ticket, True)

    def processCaptcha(self, task):
        c = task.captchaFile
        try:
            ticket, result = self.submit(c)
        except CaptchaTraderException, e:
            task.error = e.getCode()
            return

        task.data["ticket"] = ticket
        task.setResult(result)