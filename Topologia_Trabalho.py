#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call

def myNetwork():

    net = Mininet( topo=None,
                   build=False,
                   ipBase='10.0.0.0/8')

    info( '*** Adding controller\n' )
    controller=net.addController(name='controller',
                      controller=RemoteController,
                      #ip='127.0.0.1',
                      ip='10.0.0.10',
                      protocol='tcp',
                      port=6633)

    info( '*** Add switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)

    info( '*** Add hosts\n')
    auth = net.addHost('auth', cls=Host, ip='10.0.0.1', mac='00:00:00:00:00:01', defaultRoute=None)
    ev = net.addHost('ev', cls=Host, ip='10.0.0.2', mac='00:00:00:00:00:02', defaultRoute=None)
    scada = net.addHost('scada', cls=Host, ip='10.0.0.3', mac='00:00:00:00:00:03', defaultRoute=None)

    info( '*** Add links\n')
    net.addLink(auth, s1, 1, 1)
    net.addLink(scada, s1, 1, 3)
    net.addLink(ev, s1, 1, 2)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s1').start([controller])

    #info('*** Add NAT connectivity\n')
    # Add NAT connectivity
    net.addNAT().configDefault()
    #net.start()

    info( '*** Post configure switches and hosts\n')

    #Adicionando os arps manualmente
    ev.cmdPrint('arp -s 10.0.0.3 00:00:00:00:00:03')

    scada.cmdPrint('arp -s 10.0.0.1 00:00:00:00:00:01')
    scada.cmdPrint('arp -s 10.0.0.2 00:00:00:00:00:02')

    auth.cmdPrint('arp -s 10.0.0.3 00:00:00:00:00:03')

    info('*** Setting routes\n')
    auth.cmd('route add default dev auth-eth1')
    ev.cmd('route add default dev ev-eth1')
    scada.cmd('route add default dev scada-eth1')
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

