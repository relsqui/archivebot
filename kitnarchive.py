#!/usr/bin/python

from redmine import Redmine, ResourceNotFoundError
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
        self.hostname = config.get('redmine', 'host')
        self.host = Redmine(self.hostname, key=config.get('redmine', 'api_key'))
        self.project = config.get('redmine', 'default_project')
        self.infobot = config.get('redmine', 'infobot')
        self.waiting = None
        self.info = ""
        self.requester = ()
        self.got_preamble = False

    def append_page(self, title, new_text, project_id=None, comment=None, requester=None):
        if project_id == None:
            project_id = self.project
        if comment == None:
            if requester:
                comment = "Updated by {} at {}'s request.".format(self.controller.config.get('server', 'nick'), requester[0])
            else:
                comment = "Updated by {}.".format(self.controller.config.get('server', 'nick'))
        page = self.host.wiki_page.get(title, project_id=project_id)
        page.text += new_text
        page.comments = comment
        page.save()

    def archive(self):
        factoids = re_split(r'( or |\|)', self.info)[::2]
        formatted_info = "\n\n{} recorded on {} that {} is:\n* ".format(self.controller.config.get('server', 'nick'), datetime.today().date(), self.waiting) + "\n* ".join(factoids)
        try:
            self.append_page('API_test', formatted_info, requester=self.requester)
            self.controller.client.reply(self.requester[1], self.requester[0], "Done! {}/projects/{}/wiki/API_test".format(self.hostname, self.project, self.waiting))
        except ResourceNotFoundError:
            self.controller.client.reply(self.requester[1], self.requester[0], "Sorry, that wiki page doesn't exist yet.")
        self.clear()

    def clear(self):
        _log.debug("Clearing waiting stuff.")
        self.waiting = None
        self.requester = ()
        self.info = ""
        self.got_preamble = False

    @Module.handle('PRIVMSG')
    def handle_privmsg(self, client, actor, recipient, message):
        message = message.strip()
        if str(recipient) != client.user.nick:
            if message.startswith(client.user.nick):
                message = message.split(None, 1)[1]
            else:
                return

        if message == "clear" and is_admin(self.controller, client, actor):
            if self.waiting is None:
                client.reply(recipient, actor, "I'm not actually trying to archive anything right now.")
            else:
                client.reply(recipient, actor, "Okay, I'll stop trying to archive {}.".format(self.waiting))
                self.clear()

        elif message == "source":
            client.reply(recipient, actor, "I'll post it just as soon as relsqui writes me some documentation.")

        elif message == "help":
            client.reply(recipient, actor, "Usage: archive <topic>. So far I just post to a test page, as a proof of concept, but stay tuned.")

        elif self.waiting and actor == self.infobot and str(recipient) == client.user.nick:
            preamble = self.waiting + " =is= "
            if self.got_preamble:
                if message.startswith("... "):
                    message = message[4:]
                if message.endswith(" ..."):
                    message = message[:-3]
                    self.info += (message)
                else:
                    self.info += (message)
                    self.archive()
            elif message.startswith(preamble):
                message = message[len(preamble):]
                self.got_preamble = True
                if message.endswith(" ..."):
                    message = message[:-3]
                    self.info += (message)
                else:
                    self.info += (message)
                    self.archive()
            else:
                client.reply(self.requester[1], self.requester[0], "{} doesn't seem to know anything about {}.".format(self.infobot.split("!", 1)[0], self.waiting))
                self.clear()

        elif message.startswith("archive"):
            if self.waiting != None:
                client.reply(recipient, actor, "Hang on, I'm still archiving {}.".format(self.waiting))
            else:
                key = message.split(None, 1)[1]
                self.waiting = key
                self.requester = (actor.split("!", 1)[0], recipient)
                infonick = self.infobot.split("!", 1)[0]
                self.controller.client.msg(infonick, "{}: literal {}".format(infonick, key))

        else:
            client.reply(recipient, actor, "?")

module = ArchiveModule
