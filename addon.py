#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmc, xbmcaddon
import socket, json

plugin = Plugin()

CACHE_TTL = 60 * 24 # minutes

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
    return plugin.finish(get_group_items())

@plugin.cached(TTL = CACHE_TTL)
def get_group_items():
    pilight = get_pilight()
    if not pilight.connect(): return plugin_error()

    groups = pilight.groups()    
    if not groups: return plugin_error()

    items = []
    for path in groups.keys():
        items.append({
            'label': groups[path]['name'],
            'path': plugin.url_for('show_devices', group = path),
            'is_playable': False,
            'info': {
                'Year': groups[path]['order']
            }
        });

    pilight.disconnect()
    return sorted(items, key = lambda item: item['info']['Year'])


@plugin.route('/group/<group>')
def show_devices(group):
    return plugin.finish(get_devices(group))

@plugin.cached(TTL = CACHE_TTL)
def get_devices(group):
    pilight = get_pilight()
    if not pilight.connect(): return plugin_error()

    devices = pilight.devices(group)    
    if not devices: return plugin_error()

    items = []
    for path in devices.keys():
        if not type(devices[path]) is dict:
            continue

        items.append({
            'label': devices[path]['name'],
            'path': plugin.url_for('toggle_device', group = str(group), device = path),
            'is_playable': False,
            'info': {
                'Year': devices[path]['order']
            }
        });

    pilight.disconnect()
    return sorted(items, key = lambda item: item['info']['Year'])


@plugin.route('/toggle/<group>/<device>')
def toggle_device(group, device):
    pilight = get_pilight()
    if not pilight.connect(): return plugin_error()

    pilight.toggle(group, device)
    pilight.disconnect()

    plugin.redirect(plugin.url_for('show_devices', group = str(group)))


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


def get_pilight():
    return Pilight('raspberry', 5000)


def plugin_error():
    return plugin.finish([{ 'label': _('error'), 'is_playable': False }])


################################################################################
#
#   Classes
#
################################################################################


class Pilight(object):

    client = None
    host = None
    port = 0


    def __init__(self, host = '127.0.0.1', port = 5000):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port


    def connect(self):
        self.client.connect((self.host, self.port))

        msg = self._request({ 'message': 'client controller' })
        msg_key = msg.keys()[0]     

        if msg_key != 'message' or msg[msg_key] != 'accept client':
            plugin.log.warning('handshake failed (response: %s)') % (response)
            return False

        return True


    def disconnect(self):
        self.client.shutdown(socket.SHUT_RDWR)
        self.client.close()
    

    def groups(self):
        return self._config()
    

    def devices(self, group):
        groups = self._config()
        
        if group not in groups.keys():
            plugin.log.warning('device request empty for %s') % (group)
            return False

        return groups[group]


    def toggle(self, group, device):
        self._request({
            'message': 'send',
            'code': {
                'location': group,
                'device': device
            }
        })


    def _config(self):
        msg = self._request({ 'message': 'request config' })
        msg_key = msg.keys()[0]     

        if msg_key != 'config':
            plugin.log.warning('config request failed (response: %s)') % (response)
            return False
    
        return msg['config']


    def _request(self, msg):
        self.client.send(json.dumps(msg))
        response = self.client.makefile(mode = 'r').readline()

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


