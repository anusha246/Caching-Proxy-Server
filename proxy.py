'''
Code inspiration and snippets from:
https://pymotw.com/3/socket/tcp.html
https://stackoverflow.com/questions/32792333/
    python-socket-module-connecting-to-an-http-proxy-then-performing-a-get-request
'''

import sys, os, time, socket, select

#Code from https://pymotw.com/3/socket/tcp.html below
# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ('localhost', 8888)
print('starting up on {} port {}'.format(*server_address))
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

while True:
    # Wait for a connection
    print('waiting for a connection')
    connection, client_address = sock.accept()
    try:
        print('connection from', client_address)
        
        header = connection.recv(1000)
        print('received {!r}'.format(header))
        if header:
            print('sending data back to the client')

            

            
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(('www.example.org', 80))
                #s.send(header.encode('utf-8'))
                print('AAAAAAAAAAAAAAAA')
                #s.sendall(b'GET /~ylzhang/ HTTP/1.1\r\nHost: localhost:8888\r\nConnection: keep-alive\r\nUpgrade-Insecure-Requests: 1\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9\r\nSec-Fetch-Site: none\r\nSec-Fetch-Mode: navigate\r\nSec-Fetch-Dest: document\r\nAccept-Encoding: gzip, deflate, br\r\nAccept-Language: en-US,en;q=0.9\r\n\r\n')
                s.sendall(b'GET / HTTP/1.1\r\nHost: www.example.com\r\nConnection: keep-alive\r\nCache-Control: max-age=0\r\nUpgrade-Insecure-Requests: 1\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9\r\nSec-Fetch-Site: none\r\nSec-Fetch-Mode: navigate\r\nSec-Fetch-Dest: document\r\nAccept-Encoding: gzip, deflate, br\r\nAccept-Language: en-US,en;q=0.9\r\n\r\n')
                
                response = s.recv(65565)
                print('BBBBBBBBBBBBBBBB')
                print (response)
                connection.sendall(response)
                
                s.close()

                
            except socket.error as m:
               print (str(m))
               s.close()
               sys.exit(1)            
            
            
        else:
            print('no data from', client_address)
            break

    finally:
        # Clean up the connection
        connection.close()
