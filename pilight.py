#!/usr/bin/python
# -*- coding: utf-8 -*-

import json

from twisted.internet.protocol import ReconnectingClientFactory, Protocol
from twisted.internet import reactor


class PilightClientProtocol(Protocol):
    
    config = None

    def connectionMade(self):
        reactor.callLater(0, self._sendMessage,
            { 'message': 'client gui' })

    def _sendMessage(self, message):
        self.transport.write(json.dumps(message))

    def devices(self):
        return config

    def toggle(self, location, device):
        reactor.callLater(0, self._sendMessage, {
            'message': 'send',
            'code': {
                'location': location,
                'device': device
            }
        })

    def _updateConfig(self, msg):
        state = msg['values']['state']

        for location in msg['devices'].keys():
            for device in msg['devices'][location]:
                self.config[location][device]['state'] = state

        self.factory.onPilightUpdate()

    def dataReceived(self, data):
        msg = json.loads(data)
        msg_type = msg.keys()[0]

        if msg_type == 'message' and msg['message'] == 'accept client':
            reactor.callLater(0, self._sendMessage,
                { 'message': 'request config' })

        elif msg_type == 'config':
            self.config = msg['config']
            self.factory.onPilightConnected(self)

        elif msg_type == 'origin' and msg['origin'] == 'config':
            self._updateConfig(msg)


class PilightClientFactory(ReconnectingClientFactory):

    maxDelay = 2
    protocol = PilightClientProtocol

    onPilightConnected = None
    onPilightDisconnected = None
    onPilightUpdate = None

    def clientConnectionLost(self, connector, reason):
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
        self.onPilightDisconnected()

    def clientConnectionFailed(self, connector, reason):
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)
        self.onPilightDisconnected()


def onConnected(client): print 'connected'
def onDisconnected(): print 'disconnected'
def onUpdate(): print 'update'


def run(host, port = 5000, blocking = True,
        connectedCallback = onConnected,
        disconnectedCallback = onDisconnected,
        updateCallback = onUpdate):

    factory = PilightClientFactory()
    factory.onPilightConnected = connectedCallback
    factory.onPilightDisconnected = disconnectedCallback
    factory.onPilightUpdate = updateCallback

    reactor.connectTCP(host, port, factory)
    reactor.run(installSignalHandlers = blocking)


if __name__ == '__main__':
    run(host = 'raspberry')


