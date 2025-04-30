#!/usr/bin/env python

"""Ark LSP

A wrapper to expose and connect to the LSP server embeded in the Ark jupyter
kernel.
"""

import argparse
import atexit
import os
import subprocess
import sys
import tempfile

import jupyter_client


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

    msg = km.session.send(
        msg_or_type=km.session.msg("comm_open")
        | {
            "content": {
                "comm_id": "ark-lsp-server",
                "target_name": "positron.lsp",
                "data": {
                    "ip_address": "127.0.0.1",
                },
            }
        },
        stream=km.shell_channel.socket,
    )

    # NOTE: Newer versions of ark automatically allocate a port for the lsp and
    # I'm not sure we can customize that. We're going to assume that everything
    # went well and we've received a "server_started" message with a port that
    # we can pass to netcat.
    _, data = km.session.recv(km.iopub_channel.socket)
    while not data or (data.get("content").get("data") is None):
        _, data = km.session.recv(km.iopub_channel.socket)

    lsp_info = data.get("content").get("data")
    assert lsp_info.get("msg_type") == "server_started", (
        "Message type is not 'server_started.'"
    )

    subprocess.run(
        ["nc", "127.0.0.1", str(lsp_info["content"]["port"])],
        stdout=sys.stdout,
        stdin=sys.stdin,
    )
