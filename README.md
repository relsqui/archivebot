ArchiveBot
===========

IRC bot for collecting information from an infobot and posting it en masse to a Redmine wiki page.

Installation
------------

1. Install dependencies:
```
pip install -r requirements.txt
```

or, if you're not root,
```
pip install --user -r requirements.txt
```
(or use virtualenv).

2. Enable the REST web service in your Redmine instance (under Administration -> Settings -> Authentication).

3. Get your API key, or create a bot user with the appropriate read/write access and get its API key (under My Account -> API access key)

4. Do exactly one of the following, depending on how you're using archivebot.

### As a module in an existing kitn bot

* Copy just the kitn module file (kitnarchive.py) into your bot's directory.
* Add a [redmine] section to your bot's config, with the following items:
  * host (= the base URL of your redmine instance)
  * api_key (= your API key)
  * default_project (= name of the project that wiki pages belong to when not otherwise specified)
  * infobot (= the nick!user@host of the infobot to collect data from)
* If you want, add kitnarchive to your bot's autoload while you're there.
* Reload the bot's config file. Stock kitn does this by restarting. Tell your bot to `load kitnarchive` when it returns if needed.

### As a standalone bot

* Copy the example config to `bot.cfg`.
* Update everything in the server section and the redmine section (see above).
* Start the bot by running `start.sh`. (It will pass any options, like loglevel etc. through to kitn.)
