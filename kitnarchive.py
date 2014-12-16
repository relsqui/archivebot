#!/usr/bin/python

from redmine import Redmine
from redmine.exceptions import BaseRedmineError
from datetime import datetime
from logging import getLogger
from re import split as re_split
from kitnirc.modular import Module
from kitnirc.contrib.admintools import is_admin

_log = getLogger(__name__)

class ArchiveModule(Module):
    def __init__(self, *args, **kwargs):
        super(ArchiveModule, self).__init__(*args, **kwargs)
        config = self.controller.config
        if not config.has_section('redmine'):
            raise KeyError("No redmine section in configuration file.")
        for setting in ['host', 'api_key', 'default_project', 'infobot']:
            if not config.has_option('redmine', setting):
                raise KeyError("Missing required redmine setting: {}".format(setting))
        self.host = Redmine(config.get('redmine', 'host'), key=config.get('redmine', 'api_key'))
        self.project = config.get('redmine', 'default_project')
        self.infobot = config.get('redmine', 'infobot')
        self.waiting = None
        self.info = ""
        self.requester = None
        self.queue = []

    def append_page(self, title, new_text, project_id=None, comment=None, requester=None):
        if project_id == None:
            project_id = self.project
        if comment == None:
            if requester:
                comment = "Updated by {} at {}'s request.".format(self.controller.config.get('server', 'nick'), requester)
            else:
                comment = "Updated by {}.".format(self.controller.config.get('server', 'nick'))
        page = self.host.wiki_page.get(title, project_id=project_id)
        page.text += new_text
        page.comments = comment
        page.save()

    def archive(self):
        factoids = re_split(r'( or |\|)', self.info)[::2]
        formatted_info = "\n\n{} reported on {} that {} is:\n* ".format(self.controller.config.get('server', 'nick'), datetime.today().date(), self.waiting) + "\n* ".join(factoids)
        self.append_page('api_test', formatted_info, requester=self.requester)
        self.controller.client.msg(self.requester, "Done archiving {} for you!".format(self.waiting))
        self.clear()

    def clear(self):
        _log.debug("Clearing waiting stuff.")
        self.waiting = None
        self.requester = None
        self.info = ""
        for nick in self.queue:
            self.controller.client.msg(nick, "Sorry about that, all done now. You can request archives again.")
        self.queue = []

    @Module.handle('PRIVMSG')
    def handle_privmsg(self, client, actor, recipient, message):
        message = message.strip()
        if str(recipient) != client.user.nick:
            if message.startswith(client.user.nick):
                message = message.split(None, 1)[1]
            else:
                return

        if message.startswith("clear") and is_admin(self.controller, client, actor):
            if self.waiting is None:
                client.reply(recipient, actor, "I'm not actually trying to archive anything right now.")
            else:
                client.reply(recipient, actor, "Okay, I'll stop trying to archive {}.".format(self.waiting))
                self.controller.client.msg(self.requester, "Sorry, I tried to archive {} for you and gave up. :(".format(self.waiting))
                self.clear()

        elif self.waiting and actor == self.infobot and str(recipient) == client.user.nick:
            preamble = self.waiting + " =is= "
            if message.startswith(preamble):
                message = message[len(preamble):]
            if message.startswith("... "):
                message = message[4:]
            if message.endswith(" ..."):
                message = message[:-3]
                self.info += (message)
            else:
                self.info += (message)
                self.archive()

        elif message.startswith("archive"):
            if self.waiting != None:
                client.reply(recipient, actor, "Hang on, I'm still archiving {}. I'll tell you when I'm done.".format(self.waiting))
                queued = actor.split("!", 1)[0]
                if queued not in self.queue:
                    self.queue.append(queued)
            else:
                key = message.split(None, 1)[1]
                self.waiting = key
                self.requester = actor.split("!", 1)[0]
                infonick = self.infobot.split("!", 1)[0]
                _log.debug("Got a request from {} to archive {}, asking {}".format(self.requester, key, infonick))
                self.controller.client.msg(infonick, "{}: literal {}".format(infonick, key))

        else:
            client.reply(recipient, actor, "?")

module = ArchiveModule
