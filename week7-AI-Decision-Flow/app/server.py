"""
One Flask process serves both the Dash UI (at /) and the Inngest function
handler (at /api/inngest, where the Inngest dev server calls back into
this app to execute steps). Plus one small polling endpoint the frontend
uses to read run progress.

Run:
    python -m app.server
Then, in another terminal, start Inngest's dev server pointed at this app:
    npx inngest-cli@latest dev -u http://localhost:8000/api/inngest
"""
import os
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, jsonify
import inngest.flask

from app.inngest_client import client as inngest_client, run_workflow
from app import store
from app.dash_app import create_dash_app

server = Flask(__name__)

inngest.flask.serve(server, inngest_client, [run_workflow])


@server.route("/api/runs/<run_id>")
def get_run_status(run_id):
    run = store.get_run(run_id)
    if run is None:
        return jsonify({"error": "unknown run_id"}), 404
    return jsonify(run)


@server.route("/health")
def health():
    return jsonify({"status": "ok"})


dash_app = create_dash_app(server)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    server.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
