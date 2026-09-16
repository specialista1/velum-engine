import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import sys

ROOT = Path(__file__).resolve().parent
UI = ROOT / 'v08_ui' / 'index.html'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from velum_engine.negotiation_desk import NegotiationDesk

desk = NegotiationDesk()

class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type='application/json; charset=utf-8'):
        if isinstance(body, str): body = body.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/health':
            return self._send(200, json.dumps({'status':'ok','engine_version':'0.8-mock'}))
        if path in ('/', '/index.html'):
            return self._send(200, UI.read_bytes(), 'text/html; charset=utf-8')
        self._send(404, json.dumps({'error':'not found'}))

    def do_POST(self):
        path = urlparse(self.path).path
        if path != '/api/negotiation/product':
            return self._send(404, json.dumps({'error':'not found'}))
        try:
            length = int(self.headers.get('Content-Length','0'))
            payload = json.loads(self.rfile.read(length).decode('utf-8'))
            result = desk.product(**payload)
            result['action_plan'] = desk.action_plan(result)
            self._send(200, json.dumps(result, ensure_ascii=False))
        except Exception as exc:
            self._send(400, json.dumps({'status':'error','error':str(exc)}, ensure_ascii=False))

    def log_message(self, fmt, *args):
        print('[VELUM]', fmt % args)

if __name__ == '__main__':
    # HOST/PORT vem do ambiente em producao (Render, etc). Local, usa 127.0.0.1:8000 como antes.
    host = os.environ.get('HOST', '0.0.0.0' if os.environ.get('PORT') else '127.0.0.1')
    port = int(os.environ.get('PORT', 8000))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f'[VELUM] Motor iniciado em http://{host}:{port}')
    print('[VELUM] Pressione Ctrl+C para encerrar.')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
