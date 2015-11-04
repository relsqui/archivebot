#!/usr/bin/python

from redmine import Redmine, ResourceNotFoundError
from redmine.exceptions import BaseRedmineError, ForbiddenError
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
        self.target = None
        self.info = ""
        self.requester = ()
        self.got_preamble = False

    def append_page(self, new_text):
        if "/" in self.target:
            project_id, title = self.target.split("/", 1)
        else:
            project_id = self.project
            title = self.target
        try:
            page = self.host.wiki_page.get(title, project_id=project_id)
        except ForbiddenError:
            self.controller.client.reply(self.requester[1], self.requester[0], "I don't have permission to read that page!")
            self.clear()
            return

        target = "\n!>https://raw.githubusercontent.com/relsqui/archivebot/master/ArchiveBot-target.png!"
        new_text += target
        if target in page.text:
            parts = page.text.split(target, 1)
            page.text = new_text.join(parts)
        else:
            page.text += new_text
        page.comments = "Updated by {} at {}'s request.".format(self.controller.config.get('server', 'nick'), self.requester[0])
        try:
            page.save()
        except ForbiddenError:
            self.controller.client.reply(self.requester[1], self.requester[0], "I don't have permission to write to that page!")
            self.clear()
        return "{}/projects/{}/wiki/{}".format(self.hostname, project_id, title)

    def archive(self):
        factoids = re_split(r'( or |\|)', self.info)[::2]
        formatted_info = "\n\n{} recorded on {} that {} is:\n* ".format(self.controller.config.get('server', 'nick'), datetime.today().date(), self.waiting) + "\n* ".join(factoids)
        try:
            page_url = self.append_page(formatted_info)
            self.controller.client.reply(self.requester[1], self.requester[0], "Done! {} -- I didn't delete the bot entry, just to be safe; please make sure I copied everything right, then do so.".format(page_url))
        except ResourceNotFoundError:
            self.controller.client.reply(self.requester[1], self.requester[0], "Sorry, that wiki page doesn't exist yet.")
        self.clear()

    def clear(self):
        _log.debug("Clearing waiting stuff.")
        self.waiting = None
        self.target = None
        self.requester = ()
        self.info = ""
        self.got_preamble = False

    @Module.handle('PRIVMSG')
    def handle_privmsg(self, client, actor, recipient, message):
        actor_nick = actor.split("!", 1)[0]
        if actor_nick.lower().endswith("bot") and actor != self.infobot:
            _log.debug("Ignored message from {} because I think it's a bot (and not my infobot).".format(actor_nick))
            return

        message = message.strip()
        if str(recipient) != client.user.nick:
            if message.startswith(client.user.nick):
                if message.startswith(client.user.nick + "++"):
                    return
                message = message.split(None, 1)[1]
            elif actor == self.infobot and message.endswith("..."):
                client.emote(recipient, "looks up hopefully.")
                _log.debug("{} trailed off, maybe someone needs to archive?".format(self.infobot))
                return

            else:
                return

        if message == "clear" and is_admin(self.controller, client, actor):
            if self.waiting is None:
                client.reply(recipient, actor, "I'm not actually trying to archive anything right now.")
            else:
                client.reply(recipient, actor, "Okay, I'll stop trying to archive {}.".format(self.waiting))
                self.clear()

        elif message == "source":
            client.reply(recipient, actor, "https://github.com/relsqui/archivebot")

        elif message == "help":
            client.reply(recipient, actor, "Usage: 'archive <bot entry> => [<wiki_project>/]<wiki_page>', e.g. 'archive r3lsqui => f1nnre', or 'archive r3lsqui => braindump/f1nnre'. For full README, see http://bit.ly/archivebotreadme")

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
                try:
                    # Peel off "archive"
                    message = message.split(None, 1)[1]
                    key, target = message.split("=>", 1)
                    key = key.strip()
                    target = target.strip()
                    if not key or not target:
                        raise ValueError
                except (IndexError, ValueError):
                    client.reply(recipient, actor, "Syntax: 'archive <bot entry> => [<wiki_project>/]<wiki_page>'. See also help.")
                    return
                if target.startswith("/") or target.endswith("/"):
                    client.reply(recipient, actor, "The wiki page should be either just page_name, or project_name/page_name if it's not in the {} project.".format(self.project))
                    return
                self.waiting = key
                self.target = target
                self.requester = (actor.split("!", 1)[0], recipient)
                infonick = self.infobot.split("!", 1)[0]
                self.controller.client.msg(infonick, "{}: literal {}".format(infonick, key))

        elif message.startswith("sudo "):
            client.reply(recipient, actor, "Password:")

        elif message == "hunter2":
            client.reply(recipient, actor, "This incident will be reported.")

        else:
            client.reply(recipient, actor, "?")

module = ArchiveModule
