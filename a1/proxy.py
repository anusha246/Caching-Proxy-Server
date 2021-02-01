'''
Code inspiration and snippets from:
https://pymotw.com/3/socket/tcp.html
https://stackoverflow.com/questions/32792333/
    python-socket-module-connecting-to-an-http-proxy-then-performing-a-get-request
'''

import sys, os, time, socket, select

def proxy(expiry):
    
    initial_response = True
    response_body1 = None
    response_body2 = None
    
    #yellow_box = b'\x8cK\x0e\x830\x0cD\xaf\x12\xb1G\xfd\xec\x9aP\xee\x02\xd8I\xacZq\x04\xae\x128}\xd3\xd2Y\xbd\x91\xde\xcc\x90\xcd\xa6;\xe3\xb3;zJ\x80\xd5>Z\x9c\xc9\xb2\x91\x92$\xeb\xa9"8\xa3\x92\xed\xfd\x9a\xab3\x8c^\xffX\x0846\xfe\x95\x88\x14\xa2\xda\xdb\xd9\xe6iy\x85U\xde\t\xfaEXV\xbb#\xb3\x94v<\x01P\n\xcd\xfbj^\x92\xf6\xe5\\\xce\xc2\xe0\xbaQ#\x1a\xc5\xaa'
    
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

                filename = host.decode('utf-8') + ' ' \
                           + relative_url.decode('utf-8').replace('/', ',') \
                           + '.bin'
                print('Filename: {}'.format(filename))

                is_expired = True
            
                #Check if a file is expired, if it exists
                try:
                    is_expired = time.time() - os.path.getmtime(filename) >= expiry
                    print('Elapsed time is {}, expiry is {}'.format(\
                            time.time() - os.path.getmtime(filename), expiry))
                except:
                    print('')
                    print('File does not exist')

                if not is_expired:
                    with open(filename, mode='rb') as file:
                        connection.sendall(file.read())
                    print('File read successful')
                    
                else:    
                    try: #Try connecting to web server
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                        print(host)
                        print(host.decode('utf-8'))
                        s.connect((host.decode('utf-8'), 80))

                        header = header.replace(url, relative_url)
                        header = header.replace(b'localhost:8888', host)
                        print(header)
                        
                        encoding = header.split(b'Accept-Encoding: ')[1].split(b'\r\n')[0]
                        header = header.replace(encoding, b'identity')                        
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
                            
                            if initial_response:
                                response_body1 = response.split(b'<body>')[0]
                                response_body2 = response.split(b'<body>')[1]
                                
                                timestamp =  time.time()
                                fresh_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
                                fresh_time = bytes(fresh_time, encoding='utf8')
                                fresh_response = response_body1 + b'<body>' + b'<p style="z-index:9999; position:fixed; top:20px; left:20px; \
                                width:200px; height:100px; background-color:yellow; padding:10px; font-weight:bold;">FRESH VERSION \
                                AT: ' + fresh_time + b'</p>' + response_body2
                                connection.sendall(fresh_response)
                            else:
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
                            with open(filename, mode='wb') as file:
                                if initial_response:
                                    cache_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                                    cache_time = bytes(cache_time, encoding='utf8')
                                    response = response_body1 + b'<body>' + b'<p style="z-index:9999; position:fixed; top:20px; left:20px; \
                                    width:200px; height:100px; background-color:yellow; padding:10px; font-weight:bold;">CACHED VERSION AS \
                                    OF: '+ cache_time + b'</p>' + response_body2
                                    initial_response = False
                                print('Response: {}'.format(response))
                                file.write(response)
                                print('Response written successfully')
                                
                            s.close()

                    
                    #Except block below from
                    #https://stackoverflow.com/questions/32792333/
                    #python-socket-module-connecting-to-an-http-proxy-then-performing-a-get-request
                    except socket.error as m:
                       print (str(m))
                       s.close()
                       sys.exit(1)

                
                
                
            else:
                print('no data from', client_address)

        finally:
            # Clean up the connection
            connection.close()


if __name__ == "__main__":
    expiry = int(sys.argv[1])
    proxy(expiry)
