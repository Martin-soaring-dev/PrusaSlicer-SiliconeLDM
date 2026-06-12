import socket, threading, struct, sys

SOCKS5 = ('127.0.0.1', 10808)
LISTEN = ('127.0.0.1', 10809)

def socks_connect(host, port):
    s = socket.socket()
    s.settimeout(30)
    s.connect(SOCKS5)
    s.send(b'\x05\x01\x00')
    if s.recv(2) != b'\x05\x00': return None
    h = host.encode()
    s.send(b'\x05\x01\x00\x03' + bytes([len(h)]) + h + struct.pack('>H', port))
    if s.recv(10)[1] != 0: return None
    return s

def handle(c):
    try:
        data = c.recv(4096)
        if not data: return
        line = data.split(b'\r\n')[0].decode()
        parts = line.split()
        if len(parts) < 2: return
        method, url = parts[0], parts[1]
        if method == 'CONNECT':
            h, p = url.split(':')
            p = int(p)
        else:
            if url.startswith('https://'): url, p = url[8:], 443
            elif url.startswith('http://'): url, p = url[7:], 80
            else: return
            h = url.split('/')[0].split(':')[0]
            if ':' in url.split('/')[0]: p = int(url.split('/')[0].split(':')[1])
        r = socks_connect(h, p)
        if not r: c.send(b'HTTP/1.1 502\r\n\r\n'); return
        if method == 'CONNECT': c.send(b'HTTP/1.1 200\r\n\r\n')
        else: r.send(data)
        def relay(a, b):
            try:
                while True:
                    d = a.recv(8192)
                    if not d: break
                    b.send(d)
            except: pass
        t1 = threading.Thread(target=relay, args=(c, r), daemon=True)
        t2 = threading.Thread(target=relay, args=(r, c), daemon=True)
        t1.start(); t2.start()
        t1.join(60); t2.join(60)
    except: pass

srv = socket.socket()
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(LISTEN)
srv.listen(50)
print(f'Proxy: {LISTEN[0]}:{LISTEN[1]} -> SOCKS5 {SOCKS5[0]}:{SOCKS5[1]}')
while True:
    try:
        cl, _ = srv.accept()
        threading.Thread(target=handle, args=(cl,), daemon=True).start()
    except KeyboardInterrupt: break
    except: pass
