"""Small standard-library CDP transport for local Edge audit scripts."""
import base64
import hashlib
import json
import os
import socket
import struct
import time
import urllib.request


class DevTools:
    def __init__(self, port):
        pages = json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json/list'))
        url = next(p['webSocketDebuggerUrl'] for p in pages if p['type'] == 'page')
        from urllib.parse import urlsplit
        target = urlsplit(url)
        self.sock = socket.create_connection((target.hostname, target.port), timeout=20)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((f'GET {target.path} HTTP/1.1\r\nHost: {target.netloc}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n').encode())
        header = b''
        while not header.endswith(b'\r\n\r\n'):
            header += self.sock.recv(1)
        expected = base64.b64encode(hashlib.sha1((key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest())
        assert header.startswith(b'HTTP/1.1 101 ') and expected in header, header
        self.sequence = 0
        self.errors = []
        self.responses = []
        self.network_failures = []
        self.loads = 0
        self.command('Runtime.enable')
        self.command('Log.enable')
        self.command('Page.enable')
        self.command('Network.enable')

    def read(self, count):
        data = b''
        while len(data) < count:
            chunk = self.sock.recv(count-len(data))
            if not chunk:
                raise EOFError('DevTools disconnected')
            data += chunk
        return data

    def command(self, method, params=None):
        self.sequence += 1
        data = json.dumps({'id': self.sequence, 'method': method, 'params': params or {}}).encode()
        mask = os.urandom(4)
        length = len(data)
        header = bytes([0x81, 0x80 | (length if length < 126 else 126 if length < 65536 else 127)])
        if length >= 126:
            header += struct.pack('!H' if length < 65536 else '!Q', length)
        self.sock.sendall(header+mask+bytes(b ^ mask[i % 4] for i, b in enumerate(data)))
        message = b''
        while True:
            first, second = self.read(2)
            length = second & 127
            if length in (126, 127):
                length = struct.unpack('!H' if length == 126 else '!Q', self.read(2 if length == 126 else 8))[0]
            assert not second & 128
            payload = self.read(length)
            if first & 15 == 8:
                raise EOFError('DevTools closed')
            message += payload
            if not first & 128:
                continue
            event = json.loads(message)
            message = b''
            if event.get('method') == 'Page.loadEventFired':
                self.loads += 1
            elif event.get('method') == 'Network.responseReceived':
                response = event['params']['response']
                self.responses.append({'url':response['url'], 'status':response['status'],
                                       'type':event['params']['type']})
            elif event.get('method') == 'Network.loadingFailed':
                self.network_failures.append(event['params'])
            if event.get('method') == 'Runtime.exceptionThrown' or (event.get('method') == 'Log.entryAdded' and event['params']['entry']['level'] == 'error') or (event.get('method') == 'Runtime.consoleAPICalled' and event['params']['type'] == 'error'):
                self.errors.append(event)
            if event.get('id') == self.sequence:
                assert 'error' not in event, event
                return event.get('result', {})

    def evaluate(self, expression):
        result = self.command('Runtime.evaluate', {'expression': expression, 'returnByValue': True, 'awaitPromise': True})
        assert 'exceptionDetails' not in result, result
        return result.get('result', {}).get('value')

    def wait(self, expression, timeout=15):
        deadline = time.monotonic()+timeout
        while time.monotonic() < deadline:
            try:
                if self.evaluate(expression):
                    return
            except AssertionError as exc:
                if 'context' not in str(exc).lower():
                    raise
            time.sleep(.1)
        raise AssertionError(f'Browser timeout: {expression}; location={self.evaluate("location.href")}')

    def navigate(self, url):
        self.command('Page.navigate', {'url': url})
        self.wait('document.readyState === "complete"')

    def fill(self, selector, value):
        self.evaluate(f'(()=>{{const e=document.querySelector({json.dumps(selector)});if(!e)throw Error("Missing input");e.value={json.dumps(value)};e.dispatchEvent(new Event("input",{{bubbles:true}}));e.dispatchEvent(new Event("change",{{bubbles:true}}));}})()')

    def click(self, selector):
        self.evaluate(f'document.querySelector({json.dumps(selector)}).click()')
