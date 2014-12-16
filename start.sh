#!/bin/sh

./archivebot.py $* 2>>log.archivebot & tail -f log.archivebot
