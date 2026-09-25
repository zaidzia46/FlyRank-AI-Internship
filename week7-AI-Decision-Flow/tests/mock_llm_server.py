"""
Mock OpenAI-compatible server for testing app/llm.py's ask_yes_no() against
real HTTP responses, without a real provider.

MOCK_SCENARIO:
  "clean_yes"        -> always "YES"
  "clean_no"         -> always "NO"
  "messy_yes"        -> "Sure, I think the answer is YES." (extractable without repair)
  "messy_then_clean" -> first call is unparseable, repair call returns clean "NO"
  "garbage_always"   -> never contains YES or NO, even after repair
"""
import os
import json
import threading
import http.server
import socketserver

PORT = int(os.environ.get("MOCK_PORT", "8980"))
call_count = {"n": 0}


def chat_response(content: str):
    return {
        "id": "mock-1",
        "object": "chat.completion",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 50, "completion_tokens": 5, "total_tokens": 55},
    }


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        scenario = os.environ.get("MOCK_SCENARIO", "clean_yes")
        call_count["n"] += 1
        n = call_count["n"]

        if scenario == "clean_yes":
            content = "YES"
        elif scenario == "clean_no":
            content = "NO"
        elif scenario == "messy_yes":
            content = "Sure, I think the answer is YES."
        elif scenario == "messy_then_clean":
            content = "hmm, unclear, maybe?" if n == 1 else "NO"
        elif scenario == "garbage_always":
            content = "I cannot determine that from the given information."
        else:
            content = "YES"

        self._send(200, chat_response(content))

    def _send(self, status, body):
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(payload)


def start_server():
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd
