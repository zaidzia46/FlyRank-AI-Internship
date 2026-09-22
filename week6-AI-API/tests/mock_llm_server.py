import os
import time
import json
import threading
import http.server
import socketserver

PORT = int(os.environ.get("MOCK_PORT", "8935"))
call_count = {"n": 0}


def usage_block():
    return {"prompt_tokens": 120, "completion_tokens": 40, "total_tokens": 160}


def chat_response(content: str):
    return {
        "id": "mock-1",
        "object": "chat.completion",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
        "usage": usage_block(),
    }


VALID_JSON = json.dumps({"category": "billing", "urgency": "normal", "confidence": 0.9, "reason": "Test case."})
BROKEN_JSON = "{category: billing, this is not valid json"
WRONG_ENUM_JSON = json.dumps({"category": "not_a_real_category", "urgency": "normal", "confidence": 0.9, "reason": "x"})
FENCED_JSON = f"Sure! Here's the JSON:\n```json\n{VALID_JSON}\n```"


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        scenario = os.environ.get("MOCK_SCENARIO", "ok")
        call_count["n"] += 1
        n = call_count["n"]

        if scenario == "ok":
            self._send(200, chat_response(VALID_JSON))
        elif scenario == "fence":
            self._send(200, chat_response(FENCED_JSON))
        elif scenario == "wrong_enum":
            self._send(200, chat_response(WRONG_ENUM_JSON))
        elif scenario == "malformed_once":
            self._send(200, chat_response(BROKEN_JSON if n == 1 else VALID_JSON))
        elif scenario == "malformed_twice":
            self._send(200, chat_response(BROKEN_JSON))
        elif scenario == "rate_limit_then_ok":
            if n == 1:
                self._send(429, {"error": {"message": "rate limited"}}, extra_headers={"Retry-After": "0"})
            else:
                self._send(200, chat_response(VALID_JSON))
        elif scenario == "server_error_persistent":
            self._send(500, {"error": {"message": "internal error"}})
        elif scenario == "unauthorized":
            self._send(401, {"error": {"message": "invalid api key"}})
        elif scenario == "slow":
            time.sleep(2.0)
            self._send(200, chat_response(VALID_JSON))
        else:
            self._send(400, {"error": {"message": f"unknown scenario {scenario}"}})

    def _send(self, status, body, extra_headers=None):
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(payload)


def start_server():
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd


if __name__ == "__main__":
    start_server()
    print(f"mock server on :{PORT}, scenario={os.environ.get('MOCK_SCENARIO', 'ok')}")
    while True:
        time.sleep(1)
