#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmc, xbmcaddon
from twisted.internet import reactor

import pilight
import time
import signal


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


def onPilightConnected():
    print 'onPilightConnected'


def onPilightDisconnected():
    print 'onPilightDisconnected'


def onStop(num, frame):
    if num == signal.SIGINT:
        reactor.stop()


if __name__ == '__main__':
    reactor.addSystemEventTrigger(
        'during', 'onPilightConnected', onPilightConnected)

    reactor.addSystemEventTrigger(
        'during', 'onPilightDisconnected', onPilightDisconnected)

    signal.signal(signal.SIGINT, onStop)
    signal.signal(signal.SIGHUP, onStop)

    pilight.run(address = 'ws://raspberry:5001/')
    plugin.run()


