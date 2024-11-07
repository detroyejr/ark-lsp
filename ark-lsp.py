#!/usr/bin/env python

"""Ark LSP

A wrapper to expose ark's lsp server.
"""

import argparse
import atexit
import os
import random
import socket
import subprocess
import sys
import tempfile
import time

import jupyter_client


def get_open_ports(n=1):
    """Get an open port from a range."""
    result = set()
    while len(result) < n:
        port_is_closed = True
        while port_is_closed:
            port = random.sample(range(43000, 63000), 1)[0]
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                port_is_closed = sock.connect_ex(("127.0.0.1", port)) == 0
        result.add(port)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A wrapper to expose ark's LSP server."
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Print the version.",
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=1,
        help="Time to wait for the LSP server.",
    )

    parser.add_argument(
        "--no-cleanup",
        dest="cleanup",
        action="store_true",
        help="Don't cleanup ark's runtime metadata.",
    )

    args = parser.parse_args()

    if args.version:
        print("Ark 0.5.1")
        sys.exit(0)

    # Setup connection and logging information.
    tempdir = tempfile.TemporaryDirectory()

    if not args.cleanup:
        atexit.register(tempdir.cleanup)

    connection_file, connection_meta = jupyter_client.write_connection_file(
        fname=tempdir.name + "/connection.json",
        ip="127.0.0.1",
        name="ark-lsp",
    )

    # NOTE: Nix uses R_LIBS_SITE extensively to catalogue the list of available
    # R packages in your environment. If this isn't set ark will default to
    # using R_HOME which doesn't have any information about the nix store or
    # packages available in your environment.
    rpaths = subprocess.run(
        [
            "Rscript",
            "--silent",
            "-e",
            'paste(.libPaths(), collapse = ":")',
        ],
        stdout=subprocess.PIPE,
    )

    lsp = subprocess.Popen(
        [
            "ark",
            "--connection_file",
            connection_file,
            "--log",
            "{}/kernel.log".format(tempdir.name),
        ],
        start_new_session=True,
        env=os.environ.copy() | {"R_LIBS_SITE": rpaths.stdout[4:-1].decode()},
    )

    # Cleanup ark server when python exits.
    atexit.register(lsp.terminate)

    km = jupyter_client.AsyncKernelClient(
        connection_file=jupyter_client.find_connection_file(connection_file)
    )
    km.load_connection_file()
    km.start_channels()

    (lsp_port,) = get_open_ports()

    km.session.send(
        msg_or_type=km.session.msg("comm_open")
        | {
            "content": {
                "comm_id": "ark-lsp-server",
                "target_name": "positron.lsp",
                "data": {"client_address": "127.0.0.1:{}".format(lsp_port)},
            }
        },
        stream=km.shell_channel.socket,
    )

    # Give the LSP time to start.
    time.sleep(args.timeout)

    subprocess.run(
        ["nc", "127.0.0.1", str(lsp_port)],
        stdout=sys.stdout,
        stdin=sys.stdin,
    )
