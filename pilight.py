#!/usr/bin/python
# -*- coding: utf-8 -*-

import json

from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor

from autobahn.websocket import WebSocketClientFactory, \
                               WebSocketClientProtocol, \
                               connectWS


class PilightClientProtocol(WebSocketClientProtocol):
    
    config = {}

    def devices(self):
        return config

    def toggle(self, location, device):
        reactor.callLater(0, self.sendMessage, json.dumps({
            'message': 'send',
            'code': {
                'location': location,
                'device': device
            }
        }))

        print 'toggle %s:%s' % (location, device)

    def _updateConfig(self, data):
        state = data['values']['state']

        for location in data['devices'].keys():
            for device in data['devices'][location]:
                self.config[location][device]['state'] = state
                print "%s => %s" % (device, state)

        reactor.callLater(0, reactor.fireSystemEvent, 'onPilightUpdate')

    def onMessage(self, msg, binary):
        data = json.loads(msg)
        msg_type = data.keys()[0]

        if msg_type == 'config':
            self.config = data['config']
            reactor.callLater(0, reactor.fireSystemEvent, 'onPilightConnected')
            
            print 'got config'

        elif msg_type == 'origin' and data['origin'] == 'config':
            self._updateConfig(data)
    
    def connectionMade(self):
        WebSocketClientProtocol.connectionMade(self)
        reactor.callLater(0, self.sendMessage, json.dumps(
            { 'message': 'request config' }))

        print 'request config'


class PilightClientFactory(ReconnectingClientFactory, WebSocketClientFactory):

    maxDelay = 1

    def startedConnecting(self, connector):
        print 'connecting'

    def clientConnectionLost(self, connector, reason):
        print 'connection lost'
        reactor.callLater(0, reactor.fireSystemEvent, 'onPilightDisconnected')
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        print 'connection failed'
        reactor.callLater(0, reactor.fireSystemEvent, 'onPilightDisconnected')
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)


def run(address, blocking = False):
    factory = PilightClientFactory(address)
    factory.protocol = PilightClientProtocol
    factory.setProtocolOptions(version = 13)

    connectWS(factory)
    reactor.run(installSignalHandlers = blocking)


if __name__ == '__main__':
    run(address = 'ws://192.168.2.4:5000', blocking = True)


