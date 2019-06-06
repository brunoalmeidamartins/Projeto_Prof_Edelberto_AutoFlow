'''
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('127.0.0.1', 10000))
s.listen(5)
while 1:
  (clientsocket, address) = s.accept()
  #DO STH.
clientsocket.close()
'''
'''
import socket
HOST = '10.0.0.2'              # Endereco IP do Servidor
PORT = 7789           # Porta que o Servidor esta
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
orig = (HOST, PORT)
udp.bind(orig)
while True:
    msg, cliente = udp.recvfrom(1024)
    print cliente, msg
udp.close()
'''


import socket
HOST = '10.0.0.1'              # Endereco IP do Servidor
PORT = 7789           # Porta que o Servidor esta
tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
orig = (HOST, PORT)
tcp.bind(orig)
tcp.listen(1)
print 'Ouvindo na porta:', PORT
while True:
    con, cliente = tcp.accept()
    print 'Concetado por', cliente
    while True:
        msg = con.recv(1024)
        if not msg: break
        print cliente, msg
    print 'Finalizando conexao do cliente', cliente
    con.close()
