#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmc, xbmcaddon
from twisted.internet import reactor

import pilight
import time


client = None
plugin = Plugin()
STRINGS = {}


@plugin.route('/')
def index():
    return plugin.finish([
        { 'label': 'Video', 'path': 'video.mp4', 'is_playable': True }
    ])


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        plugin.log.warning('String is missing: %s' % string_id)
        return string_id


def onPilightDisconnected():
    client = None


def onPilightConnected(c):
    client = c
    plugin.run()


if __name__ == '__main__':
    pilight.configure(host = 'raspberry', 
        connectedCallback = onPilightConnected, 
        disconnectedCallback = onPilightDisconnected)

    reactor.run()


