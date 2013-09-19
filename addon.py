#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, ListItem, xbmc, xbmcaddon
import socket, json

plugin = Plugin()

CACHE_TTL = 0 # minutes

STRINGS = {
    'error': 30001
}


################################################################################
#
#   Routes
#
################################################################################


@plugin.route('/')
def show_groups():
    pilight = _pilight()
    if not pilight.connect(): return _error()

    groups = pilight.groups()    
    if not groups: return plugin.finish(_error())

    items = []
    for path in groups.keys():
        items.append({
            'label': groups[path]['name'],
            'path': plugin.url_for('show_devices', group = path),
            'info': { 'Year': groups[path]['order'] }
        })

    pilight.disconnect()
    return plugin.finish(
        sorted(items, key = lambda item: item['info']['Year']))


@plugin.route('/group/<group>/')
def show_devices(group):
    pilight = _pilight()
    if not pilight.connect(): return plugin.finish(_error())

    devices = pilight.devices(group)    
    if not devices: return _error()

    if 'toggle' in plugin.request.args:
        pilight.toggle(group, plugin.request.args['toggle'][0])
        del plugin.request.args['toggle']

    items = []
    for path in devices.keys():
        if not type(devices[path]) is dict:
            continue

        if devices[path]['state'] == 'on':
            icon = _image('light_on')
        else:
            icon = _image('light_off')

        items.append({
            'label': devices[path]['name'],
            'icon': icon,
            'thumbnail': icon,
            'path': plugin.url_for('show_devices', group = group, toggle = path),
            'info': { 'Year': devices[path]['order'] }
        })

    pilight.disconnect()
    return plugin.finish(
        sorted(items, key = lambda item: item['info']['Year']))


################################################################################
#
#   Helper
#
################################################################################



def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        plugin.log.warning('String is missing: %s' % string_id)
        return string_id


def _image(image):
    return 'special://home/addons/%s/resources/media/%s.png' % \
        (plugin._addon.getAddonInfo('id'), image)


def _pilight():
    return Pilight('raspberry', 5000)


def _error():
    return [{ 'label': _('error'), 'is_playable': False }]


################################################################################
#
#   Classes
#
################################################################################


class Pilight(object):

    client = None
    host = None
    port = 0
    config = None


    def __init__(self, host = '127.0.0.1', port = 5000):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port


    def connect(self):
        self.client.connect((self.host, self.port))
        msg = self._request({ 'message': 'client controller' })

        if 'message' not in msg or msg['message'] != 'accept client':
            plugin.log.error('handshake failed')
            return False

        msg = self._request({ 'message': 'request config' })

        if 'config' not in msg:
            plugin.log.error('config request failed')
            return False
    
        self.config = msg['config']

        return True


    def disconnect(self):
        self.client.shutdown(socket.SHUT_RDWR)
        self.client.close()
    

    def groups(self):
        return self.config
    

    def devices(self, group):
        if not self.config or group not in self.config:
            plugin.log.error('device request empty')
            return False

        return self.config[group]


    def toggle(self, group, device):
        if self.config[group][device]['state'] == 'on':
            self.config[group][device]['state'] = 'off'
        else:
            self.config[group][device]['state'] = 'on'

        self._request({
            'message': 'send',
            'code': {
                'location': group,
                'device': device
            }
        })


    def _request(self, msg):
        self.client.send(json.dumps(msg))
        response = self.client.makefile(mode = 'r').readline().strip()

        try:
            return json.loads(response)
        except:
            return {}
        

################################################################################
#
#   Main
#
################################################################################


if __name__ == '__main__':
    plugin.run()


