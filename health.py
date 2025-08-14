#!/usr/bin/env python3
"""
Health check endpoint for Railway deployment monitoring.
This script can be called independently or integrated into the main app.
"""

import json
import sys
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
import os

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks."""
    
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            # Return healthy status
            response = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "service": "RETS Dashboard",
                "version": "1.0.0",
                "uptime": time.time() - start_time
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress log messages
        pass

# Global start time for uptime calculation
start_time = time.time()

def start_health_server(port=8081):
    """Start a simple health check server on a different port."""
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        print(f"Health check server starting on port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"Failed to start health server: {e}")

def run_health_check():
    """Run health check as a background thread."""
    health_port = int(os.environ.get('HEALTH_PORT', 8081))
    health_thread = threading.Thread(target=start_health_server, args=(health_port,), daemon=True)
    health_thread.start()
    return health_thread

if __name__ == "__main__":
    # Can be run standalone for testing
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    start_health_server(port)