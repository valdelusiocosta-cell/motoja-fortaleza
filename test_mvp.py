#!/usr/bin/env python3
"""Smoke tests for the local API without external dependencies or a network port."""
import json
import os
import socket
import tempfile
from pathlib import Path

import server


def call(path, method="GET", payload=None, token=None):
    client, worker = socket.socketpair()
    body = json.dumps(payload).encode() if payload is not None else b""
    headers = [f"{method} {path} HTTP/1.1", "Host: local", f"Content-Length: {len(body)}", "Content-Type: application/json", "Connection: close"]
    if token:
        headers.append(f"Authorization: Bearer {token}")
    client.sendall(("\r\n".join(headers) + "\r\n\r\n").encode() + body)
    client.shutdown(socket.SHUT_WR)
    server.Handler(worker, ("local", 0), object())
    worker.close()
    raw = b""
    while True:
        chunk = client.recv(65536)
        if not chunk:
            break
        raw += chunk
    client.close()
    head, content = raw.split(b"\r\n\r\n", 1)
    status = int(head.splitlines()[0].split()[1])
    return status, json.loads(content)


def main():
    with tempfile.TemporaryDirectory() as folder:
        server.DB_PATH = Path(folder) / "test.sqlite3"
        server.init_db()
        assert call("/api/health")[0] == 200
        code, passenger = call("/api/auth/login", "POST", {"identity": "passageiro@demo.motoja.local", "password": "demo1234"})
        assert code == 200
        passenger_token = passenger["token"]
        assert call("/api/quote", "POST", {"origin": "Aldeota", "destination": "Centro"})[0] == 200
        code, ride = call("/api/rides", "POST", {"origin": "Aldeota", "destination": "Centro", "paymentMethod": "Pix"}, passenger_token)
        assert code == 201 and ride["status"] == "searching"
        ride_id = ride["id"]
        _, driver = call("/api/auth/login", "POST", {"identity": "motorista@demo.motoja.local", "password": "demo1234"})
        driver_token = driver["token"]
        assert call("/api/driver/online", "POST", {"online": True}, driver_token)[0] == 200
        for action, expected in (("accept", "accepted"), ("start", "in_progress"), ("finish", "finished")):
            code, ride = call(f"/api/rides/{ride_id}/{action}", "POST", {}, driver_token)
            assert code == 200 and ride["status"] == expected
        assert call(f"/api/rides/{ride_id}/start", "POST", {}, driver_token)[0] == 409
        code, admin = call("/api/auth/login", "POST", {"identity": "admin@demo.motoja.local", "password": "demo1234"})
        assert code == 200
        summary = call("/api/admin/summary", token=admin["token"])
        assert summary[0] == 200 and summary[1]["finishedRides"] == 1
        print("OK: health, auth, quote, ride state machine, driver and admin endpoints")


if __name__ == "__main__":
    main()
