"""Run the backend for the iPhone on IPv4 and IPv6 at once.

    python -m scripts.serve               # port 8000
    python -m scripts.serve --port 8001

The app reaches the Mac by its Bonjour name (BUSOFT-MB30-7.local), which
resolves to IPv4 on normal Wi-Fi and only to IPv6 on an IPv6-only mobile
hotspot. `uvicorn --host 0.0.0.0` listens on IPv4 only and `--host ::` on
IPv6 only, so this binds one dual-stack socket and hands it to uvicorn.
"""

import argparse
import socket

import uvicorn


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    sock = socket.create_server(
        ("::", args.port),
        family=socket.AF_INET6,
        dualstack_ipv6=True,
        reuse_port=False,
    )
    print(f"Listening on IPv4 and IPv6, port {args.port}")
    server = uvicorn.Server(uvicorn.Config("app.main:app", port=args.port))
    server.run(sockets=[sock])


if __name__ == "__main__":
    main()
