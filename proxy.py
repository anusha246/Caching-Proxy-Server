'''
Code inspiration and snippets from:
https://pymotw.com/3/socket/tcp.html
https://stackoverflow.com/questions/32792333/
    python-socket-module-connecting-to-an-http-proxy-then-performing-a-get-request
'''

import sys, os, time, socket, select

# Server code from https://pymotw.com/3/socket/tcp.html below
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

            first_line = header.split(b'\n')[0]
            url = first_line.split(b' ')[1]
            
            host = url.split(b'/')[1]
            
            relative_url = b''
            for i in range(2, len(url.split(b'/'))):
                relative_url += b'/' + url.split(b'/')[i]

            if relative_url == b'':
                relative_url = b'/'

        
            #Try sending cached response, if it exists    
            try:
                filename = host.decode('utf-8') + ' ' + \
                           relative_url.decode('utf-8').replace('/', ',')
                print(filename)
                file = open(filename + ".bin", mode='rb')
                connection.sendall(file.read())
                print('File read successful')

            except: #File failed to open, may not exist
                try: #Try connecting to web server
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                    print(host)
                    print(host.decode('utf-8'))
                    s.connect((host.decode('utf-8'), 80))

                    header = header.replace(url, relative_url)
                    header = header.replace(b'localhost:8888', host)
                    print(header)
                    
                    s.sendall(header)
                    print('Header sent successfully')
                    

                    response = s.recv(65565)

                    response_header = response.split(b'\r\n\r\n')[0]

                    print(response)

                    try:
                        byte_content_length = response_header.split(b'Content-Length: ')[1].split(b'\r\n')[0]
                        content_length = int(byte_content_length.decode('utf-8'))

                        content = response.split(b'\r\n\r\n')[1]
                        while len(content) != content_length:
                            print('Content length: {}, needed len: {}'.format(len(content), content_length))
                            content += s.recv(65565)

                        response = response_header + b'\r\n\r\n' + content #this is the full response now

                        print(response)

                        connection.sendall(response)
                        print('Sent response to client')
                        
                    except: #HTTP code 304 or Content-Length not specified
                        print('HTTP code 304 or Content-Length not specified')

                        if b'200 OK' in response:

                            while True:
                                incoming = s.recv(65565)
                                if len(incoming) == 0:
                                    break;
                                print (incoming)
                                print('Receieved incoming data from web server')
                                response += incoming

                        connection.sendall(response)
                        
                    finally:

                        #Write the response to file
                        try:
                            filename = host.decode('utf-8') + ' ' + \
                                       relative_url.decode('utf-8').replace('/', ',')
                            file = open(filename + ".bin", mode='wb')
                            print(response)
                            file.write(response)
                            
                            print('Response written successfully')
                        finally:
                            file.close()

                            
                        s.close()

                
                #Except block below from
                #https://stackoverflow.com/questions/32792333/
                #python-socket-module-connecting-to-an-http-proxy-then-performing-a-get-request
                except socket.error as m:
                   print (str(m))
                   s.close()
                   sys.exit(1)

            finally:
                file.close()
            
            
        else:
            print('no data from', client_address)
            #break

    finally:
        # Clean up the connection
        connection.close()
