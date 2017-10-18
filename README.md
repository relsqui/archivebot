ArchiveBot
===========

IRC bot for collecting information from an infobot and posting it en masse to a Redmine wiki page.

Usage
-----
* Copy an infobot entry to a wiki page: `ArchiveBot: archive my bot entry => my_wiki_page`
* Optionally, specify the project: `ArchiveBot: archive my bot entry => my_project/my_page`

The first time ArchiveBot appends to a page (that it knows of), it will add the information it's archiving to the end of the page and leave an invisible trace there for itself to find later. Each time it archives to the same page thereafter, it will put the new information wherever the trace is, so you can put other things after that point and all the archived information will stay together. You can also move or delete the trace if you prefer, and ArchiveBot will act like it's never seen the page before.

Installation
------------

* Install dependencies with `pip install -r requirements.txt` or the virtualenv equivalent.
* Enable the REST web service in your Redmine instance (under Administration -> Settings -> Authentication).
* Get your API key, or create a bot user with the appropriate read/write access and get its API key (under My Account -> API access key)
* Do exactly one of the following, depending on how you're using archivebot.

### as a module in an existing kitn bot:

* Copy just the kitn module file (`kitnarchive.py`) into your bot's directory.
* Add a [redmine] section to your bot's config, with the following items:
  * host (= the base URL of your redmine instance)
  * api_key (= your API key)
  * default_project (= name of the project that wiki pages belong to when not otherwise specified)
  * infobot (= the nick!user@host of the infobot to collect data from)
* If you want, add kitnarchive to your bot's autoload while you're there.
* Reload the bot's config file. Stock kitn does this by restarting. Tell your bot to `load kitnarchive` when it returns if needed.

### as a standalone bot:

* Copy the example config to `bot.cfg`.
* `mkdir modules`
* `echo '#' > modules/__init__.py`
* `ln -s kitnarchive.py modules/kitnarchive.py`
* Update everything in the server section and the redmine section (see above).
* Start the bot by running `start.sh`. (It will pass any options, like loglevel etc. through to kitn.)

Assumptions
-----------

ArchiveBot assumes the following about its environment:
* It can get a full factoid listing for "thing" from its infobot by PMing it "botnick: literal thing"
* If the infobot has that key, the reply will begin with "thing =is= "
  * If it doesn't, the infobot will reply with something that doesn't begin that way.
* Multiple entries for the same key are separated by either pipes or the word "or"
* An entry that spans multiple lines has " ..." at the end of all but the last one. Some lines may also begin with "... "
* The Redmine wiki page which is the archive target already exists.

Potential Surprises
-------------------

ArchiveBot can't distinguish between a semantic "or" in the middle of a factoid and the "or" used to separate them. This isn't a bug, exactly, since it has no possible way to tell the difference and thus it won't be fixed.

ArchiveBot also doesn't delete the entry from the infobot when it's done archiving. It errs on the side of not destroying data and leaves that for you to do afterwards.

Finally, ArchiveBot verifies the hostmask of the infobot it's told to talk to, not just the nick. This is to prevent people from using /nick to feed it lies, but it means that if the infobot's hostmask legitimately changes, ArchiveBot's configuration will need to be updated.

See also [issues](https://github.com/relsqui/archivebot/issues).
