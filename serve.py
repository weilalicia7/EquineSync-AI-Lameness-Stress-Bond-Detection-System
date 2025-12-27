#!/usr/bin/env python3
"""
Simple HTTP server for EquineSync dashboard
Serves index.html at localhost:5180
"""

import http.server
import socketserver
import os

PORT = 5180
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

if __name__ == "__main__":
    os.chdir(DIRECTORY)

    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print("="*70)
        print(f"  EquineSync Dashboard Server")
        print("="*70)
        print(f"\n  Serving at: http://localhost:{PORT}")
        print(f"  Directory: {DIRECTORY}")
        print(f"\n  Open in browser: http://localhost:{PORT}/index.html")
        print(f"\n  Press Ctrl+C to stop\n")
        print("="*70)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped.")
