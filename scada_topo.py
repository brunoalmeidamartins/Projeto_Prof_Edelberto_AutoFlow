from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.node import RemoteController
# from mininet.cli import CLI
from mininet.link import TCLink
from time import sleep
from sys import argv

SRC_DIR = ''
LOGS = SRC_DIR + 'logs/'
MMS = SRC_DIR + 'libiec61850-1.2/uff/2con/'
SCADA = MMS + 'scada_yona/'
EV = MMS + 've_yona/'
HOSTAPD = SRC_DIR + 'hostapd-2.6-auth/hostapd/'
G_ARP = SRC_DIR
WPA = SRC_DIR + 'wpa_supplicant/'
SCRIPTS = WPA + 'scripts/'

STATIC_ARP_TABLE = True

# app.exe > save_to.log 2>&1 &
# editcap -D 100 any.pcap any_2.pcap
ANY = False


class SCADA_Topology(Topo):
    def __init__(self, number_of_evs=1):
        Topo.__init__(self)

        scada = self.addHost('scada', ip='10.0.0.3/8', mac='00:00:00:00:00:03')
        auth = self.addHost(
            'auth', ip='10.0.0.1/8', mac='00:00:00:00:00:01',
            inNamespace=False)
        server_switch = self.addSwitch('s1')
        ev_switch = self.addSwitch('s2')

        # 10 Mbps, 2.5ms delay
        # internet = dict(bw=1000)
        internet = dict(bw=10, delay='2.5ms')
        # switches = dict(bw=1000)
        switches = dict(bw=100, delay='0.1ms')

        # server
        self.addLink(scada, server_switch, **internet)
        self.addLink(auth, server_switch, **internet)

        # switches
        self.addLink(server_switch, ev_switch, **switches)

        # evs
        for num in range(4, number_of_evs + 4):
            ev = self.addHost(
                'ev{}'.format(num),
                ip='10.0.0.{}/8'.format(num),
                mac='00:00:00:00:00:{:02}'.format(num))
            self.addLink(ev, ev_switch, **internet)


def log(
        name, command=None, location=None, exe=None,
        conf=None, ext=None, do_log=True, log_folder=None):
    msg = command + ' ' if command else ''
    msg += (location if location else '') + exe + ' ' if exe else ''
    msg += (location if location else '') + conf + ' ' if conf else ''
    msg += '> ' + LOGS + (
        log_folder + '/' if log_folder else '') if do_log else ''
    print msg
    msg += name
    msg += ('.' + ext if ext else '.log')
    msg += ' 2>&1 &' if do_log else ''
    return msg


def main(number_of_evs=1):
    topo = SCADA_Topology(number_of_evs)
    mn = Mininet(topo=topo, controller=None, link=TCLink)
    mn.addController(
        #'c0', controller=RemoteController, ip='10.0.2.15', port=6633)
        'c0', controller=RemoteController, ip='127.0.0.1', port=6633)
    mn.start()
    auth, scada, c0 = mn.get('auth', 'scada', 'c0')
    evs = []
    for num in range(4, number_of_evs + 4):
        if STATIC_ARP_TABLE:
            # static arp
            ev = mn.get('ev{}'.format(num))
            ev.cmdPrint(
                'arp -s 10.0.0.3 00:00:00:00:00:03')
            scada.cmdPrint(
                'arp -s 10.0.0.{0} 00:00:00:00:00:{0:02}'.format(num))
            evs.append(ev)

    # cleaning system up
    c0.cmd('killall -9 freeradius')
    c0.cmd('rm /var/run/hostapd/auth-eth0')
    c0.cmd('rm /var/run/wpa_supplicant/scada-eth0')
    c0.cmd('rm /var/run/wpa_supplicant/ev*-eth0')
    c0.cmd('mkdir {}wpa'.format(LOGS))
    c0.cmd('mkdir {}pcap'.format(LOGS))
    c0.cmd('mkdir {}iec'.format(LOGS))

    for h in mn.hosts:
        # print "disable ipv6"
        h.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        h.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        h.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")

    for sw in mn.switches:
        # print "disable ipv6"
        sw.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        sw.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        sw.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")

    # capturing traffic
    if ANY:
        c0.cmdPrint(
            'tcpdump -i any -w {}pcap/any.pcap port not 53 &'.format(LOGS))
    else:
        c0.cmdPrint(  # do not read DNS packets
            'tcpdump -i lo -w {}pcap/openflow.pcap port 6633 &'.format(LOGS))
        c0.cmdPrint(  # do not read DNS packets
            'tcpdump -i lo -w {}pcap/radius.pcap udp and port not 53 &'.format(
                LOGS))
        auth.cmdPrint(
            'tcpdump -i auth-eth0 -w {}pcap/auth.pcap &'.format(LOGS))

        for num, ev in enumerate(evs):
            ev.cmdPrint(
                'tcpdump -i ev{0}-eth0 -w {1}pcap/ev{0}.pcap &'.format(
                    num + 4, LOGS))
        scada.cmdPrint(
            'tcpdump -i scada-eth0 -w {}pcap/scada.pcap &'.format(LOGS))

    sleep(0.5)

    # setting up scada
    scada.cmdPrint(log(
        'scada', log_folder='iec', location=SCADA, exe='./scada_yona.exe'))

    # setting up authentication server
    auth.cmdPrint(log('radius', log_folder='wpa', command='freeradius -X'))
    auth.cmdPrint(log(
        'hostapd', location=HOSTAPD, exe='./hostapd',
        log_folder='wpa', conf='hostapd.conf -i auth-eth0'))
    auth.cmdPrint(log(
        'g_arp', log_folder='wpa', command='python g_arp.py', location=G_ARP))

    # authenticating
    if not STATIC_ARP_TABLE:
        scada.cmdPrint(log(
            'arp_scada',
            command='python g_arp.py scada-eth0 10.0.0.3 00:00:00:00:00:03',
            location=G_ARP))
    scada.cmdPrint(log(
        'wpa_scada', command='wpa_supplicant -D wired -c',
        log_folder='wpa',
        location=WPA, conf='scada.conf -i scada-eth0'))

    for num, ev in enumerate(evs):
        ev.cmdPrint(log(
            'wpa_ev{}'.format(num + 4),
            log_folder='wpa',
            command='wpa_supplicant -D wired -c',
            location=WPA,
            conf='ev{0}.conf -i ev{0}-eth0'.format(num + 4)))

    sleep(0.5)
    for num, ev in enumerate(evs):
        ev.cmdPrint(log(
            'ev{}'.format(num + 4),
            log_folder='iec',
            command='wpa_cli -iev4-eth0 -a',
            location=SCRIPTS,
            conf='ev{0}.sh'.format(num + 4)))

    sleep_time = {
        0: 5, 1: 7, 2: 9, 3: 10, 4: 13, 5: 15,
        6: 18, 7: 19, 8: 19, 9: 20, 10: 20}

    sleep(sleep_time[number_of_evs])
    c0.cmdPrint('killall -2 tcpdump')
    c0.cmdPrint('kill -2 $(pidof ve_yona.exe)')
    c0.cmdPrint('kill -2 $(pidof scada_yona.exe)')
    c0.cmdPrint('kill -2 $(pidof wpa_cli)')
    c0.cmdPrint('kill -2 $(pidof wpa_supplicant)')
    c0.cmdPrint('kill -2 $(pidof hostapd)')
    c0.cmdPrint('kill -9 $(pidof freeradius)')
    c0.cmdPrint(log('flows_s1', command='ovs-ofctl dump-flows s1'))
    c0.cmdPrint(log('flows_s2', command='ovs-ofctl dump-flows s2'))
    # CLI(mn)
    mn.stop()


topos = {'scada_topo': (lambda: SCADA_Topology())}

if __name__ == '__main__':
    setLogLevel('debug')
    # setLogLevel('info')
    # setLogLevel('critical')
    main(int(argv[1])) if len(argv) == 2 else main()
