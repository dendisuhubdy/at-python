import random
import socket
import hashlib
import threading
from BitTornado.Client.download_bt1 import BT1Download, defaults, \
    parse_params, get_usage, get_response
from BitTornado.Network.RawServer import RawServer
from BitTornado.Network.SocketHandler import UPnP_ERROR
from BitTornado.Meta.bencode import bencode
from BitTornado.Network.natpunch import UPnP_test
from BitTornado.Application.ConfigDir import ConfigDir
from BitTornado.Application.PeerID import createPeerID
import urllib

def error(errorMsg):
    print(errorMsg)

def finish():
    print('Done')

def display(self, dpflag=threading.Event(), fractionDone=None,
            timeEst=None, downRate=None, upRate=None, activity=None,
            statistics=None, **kws):
    print('tick')

def get(infohash):
    download([infohash])
    return infohash


def download(params):
    torrentFilePath = params[0] + '.torrent'
    urllib.urlretrieve('http://academictorrents.com/download/' + torrentFilePath, torrentFilePath)
    downloadTorrent([torrentFilePath])


def downloadTorrent(params):
    while 1:
        configdir = ConfigDir('downloadheadless')
        defaultsToIgnore = ['responsefile', 'url', 'priority']
        configdir.setDefaults(defaults, defaultsToIgnore)
        configdefaults = configdir.loadConfig()
        defaults.append(
            ('save_options', 0, 'whether to save the current options as the '
                'new default configuration (only for btdownloadheadless.py)'))
        try:
            config = parse_params(params, configdefaults)
        except ValueError as e:
            print ('error: {}\nrun with no args for parameter explanations'.format(e))
            break
        if not config:
            print (get_usage(defaults, 80, configdefaults))
            break
        if config['save_options']:
            configdir.saveConfig(config)
        configdir.deleteOldCacheData(config['expire_cache_data'])

        myid = createPeerID()
        random.seed(myid)

        doneflag = threading.Event()

        def disp_exception(text):
            print (text)
        rawserver = RawServer(
            doneflag, config['timeout_check_interval'], config['timeout'],
            ipv6_enable=config['ipv6_enabled'],
            errorfunc=disp_exception)
        upnp_type = UPnP_test(config['upnp_nat_access'])
        while True:
            try:
                listen_port = rawserver.find_and_bind(
                    config['minport'], config['maxport'], config['bind'],
                    ipv6_socket_style=config['ipv6_binds_v4'],
                    upnp=upnp_type, randomizer=config['random_port'])
                break
            except socket.error as e:
                if upnp_type and e == UPnP_ERROR:
                    print ('WARNING: COULD NOT FORWARD VIA UPnP')
                    upnp_type = 0
                    continue
                print ("error: Couldn't listen - " + str(e))
                return

        response = get_response(config['responsefile'], config['url'], error)
        if not response:
            break

        infohash = hashlib.sha1(bencode(response['info'])).digest()

        dow = BT1Download(display, finish, error, disp_exception, doneflag, config,
            response, infohash, myid, rawserver, listen_port, configdir)

        if not dow.initFiles(old_style=True):
            break
        if not dow.startEngine():
            dow.shutdown()
            break
        dow.startRerequester()
        dow.autoStats()

        if not dow.am_I_finished():
            rawserver.listen_forever(dow.getPortHandler())
            dow.shutdown()
        break
    try:
        rawserver.shutdown()
    except Exception:
        pass

