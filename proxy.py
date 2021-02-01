'''
Code inspiration and snippets from:
https://pymotw.com/3/socket/tcp.html
https://stackoverflow.com/questions/32792333/
    python-socket-module-connecting-to-an-http-proxy-then-performing-a-get-request

Steps 1, 3, 4 and 5 have been completed, however step 2 has not.
It was never able to be fully implemented because of confusion 
around how the line 'readable, writable, exceptional = 
select.select(inputs, outputs, inputs)' was operating. It appeared to
arbitrarily add sockets to writable as well as add multiple sockets to
writable even when there is only a single socket that was having information
written to it. Due to this step 2 was left unimplemented and we moved our 
attention to later steps.
'''

import sys, os, time, socket, select

def proxy(expiry):

    response_body1 = None
    response_body2 = None
    body_tag = None
    content_length = None
    
    # Server code from https://pymotw.com/3/socket/tcp.html below
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the port
    server_address = ('localhost', 8888)
    
    sock.bind(server_address)

    # Listen for incoming connections
    sock.listen(1)

    while True:
        # Wait for a connection
        
        connection, client_address = sock.accept()
        try:
            header = connection.recv(1000)
            
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

                is_expired = True
            
                #Check if a file is expired, if it exists
                try:
                    is_expired = time.time() - os.path.getmtime(filename) >= expiry
                    
                except:
                    pass #File does not exist

                if not is_expired:
                    with open(filename, mode='rb') as file:
                        connection.sendall(file.read())
  
                else:    
                    try: #Try connecting to web server
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                        s.connect((host.decode('utf-8'), 80))

                        header = header.replace(url, relative_url)
                        header = header.replace(b'localhost:8888', host)
                        
                        encoding = header.split(b'Accept-Encoding: ')[1].split(b'\r\n')[0]
                        header = header.replace(encoding, b'identity')                        
                        s.sendall(header)

                        response = s.recv(65565)

                        response_header = response.split(b'\r\n\r\n')[0]

                        content_type = response_header.split(b'Content-Type: ')[1].split(b'\r\n')[0]
                        is_html = b'text/html' in content_type

                        try:
                            byte_content_length = response_header.split(b'Content-Length: ')[1].split(b'\r\n')[0]
                            content_length = int(byte_content_length.decode('utf-8'))

                            content = response.split(b'\r\n\r\n')[1]
                            while len(content) != content_length:
                                content += s.recv(65565)

                            response = response_header + b'\r\n\r\n' + content #this is the full response now
      
                        except: #HTTP code 304 or Content-Length not specified
                            if b'200 OK' in response:
                                while True:
                                    incoming = s.recv(65565)
                                    if len(incoming) == 0:
                                        break;
                                   
                                    response += incoming
                            
                        finally:
                            if is_html:
                                pre_body = response.split(b'<body')[0]
                                post_body = response.split(b'<body')[1]
                                in_body = post_body.split(b'>')[0]
                                body_tag = b'<body' + in_body + b'>'
                                
                                response_body1 = response.split(body_tag)[0]
                                response_body2 = response.split(body_tag)[1]
                                
                                timestamp =  time.time()
                                fresh_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
                                fresh_time = bytes(fresh_time, encoding='utf8')

                                if content_length:
                                    content_length += 251
                                    response_body1 = response_body1.replace(b'Content-Length: ' +
                                                                            byte_content_length,
                                                                            b'Content-Length: ' +
                                                                            bytes(str(content_length),encoding='utf8'))
                                    
                                fresh_response = response_body1 + body_tag + b'<p style="z-index:9999; position:fixed; top:20px; left:20px; \
                                width:200px; height:100px; background-color:yellow; padding:10px; font-weight:bold;">FRESH VERSION \
                                AT: ' + fresh_time + b'</p>' + response_body2

                                connection.sendall(fresh_response)
                            else:
                                connection.sendall(response)
                                
                            #Write the response to file
                            with open(filename, mode='wb') as file:
                                if is_html:
                                    cache_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                                    cache_time = bytes(cache_time, encoding='utf8')

                                    if content_length:
                                        response_body1 = response_body1.replace(b'Content-Length: ' +
                                                                                bytes(str(content_length),encoding='utf8'),
                                                                                b'Content-Length: ' +
                                                                                bytes(str(content_length + 12),encoding='utf8'))
                                    
                                    response = response_body1 + body_tag + b'<p style="z-index:9999; position:fixed; top:20px; left:20px; \
                                    width:200px; height:100px; background-color:yellow; padding:10px; font-weight:bold;">CACHED VERSION AS \
                                    OF: '+ cache_time + b'</p>' + response_body2
 
                                
                                file.write(response)
                                
                            s.close()

                    
                    #Except block below from
                    #https://stackoverflow.com/questions/32792333/
                    #python-socket-module-connecting-to-an-http-proxy-then-performing-a-get-request
                    except socket.error as m:
                        s.close()
                        sys.exit(1)
                
            else:
                pass

        finally:
            # Clean up the connection
            connection.close()


if __name__ == "__main__":
    expiry = int(sys.argv[1])
    proxy(expiry)
