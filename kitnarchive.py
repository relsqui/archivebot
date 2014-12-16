#!/usr/bin/python

from redmine import Redmine
from redmine.exceptions import BaseRedmineError
from datetime import datetime
from logging import getLogger
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

    def append_page(self, title, new_text, project_id=None, comment=None):
        if project_id == None:
            project_id = self.project
        if comment == None:
            comment = "Updated by {}.".format(self.controller.config.get('server', 'nick'))
        page = self.host.wiki_page.get(title, project_id=project_id)
        page.text += new_text
        page.comments = comment
        page.save()

    @Module.handle('PRIVMSG')
    def handle_privmsg(self, client, actor, recipient, message):
        message = message.strip()
        if str(recipient) != client.user.nick:
            if message.startswith(client.user.nick):
                message = message.split(None, 1)[1]
            else:
                return

        if message.startswith("test") and is_admin(self.controller, client, actor):
            self.append_page('api_test', "\n* {} - scripted update at {}'s request.".format(datetime.now(), actor))
            client.reply(recipient, actor, "Okay, posted a test to {}/projects/{}/wiki/api_test".format(self.controller.config.get('redmine', 'host'), self.project))
        else:
            client.reply(recipient, actor, "?")

module = ArchiveModule
