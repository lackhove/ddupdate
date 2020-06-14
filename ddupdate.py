#!/bin/env python

import argparse
import json
import logging
import subprocess
import sys
import time
from configparser import ConfigParser
from datetime import datetime, timedelta
from pathlib import Path

import requests

logger = logging.getLogger("playlistSync")
ch = logging.StreamHandler(sys.stdout)
logger.addHandler(ch)


class NoIpError(Exception):
    pass


class IpUpdateError(Exception):
    pass


def get_ip(net_dev):
    command = [
        "ip",
        "-j",
        "-6",
        "addr",
        "list",
        "dev",
        net_dev,
        "scope",
        "global",
        "-tentative",
        "-deprecated",
        "-dadfailed",
    ]
    proc = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8"
    )
    if proc.returncode != 0:
        raise NoIpError("ip execution failed: " + proc.stdout + " " + proc.stderr)

    reply = json.loads(proc.stdout)
    for dev in reply:
        for addr in dev["addr_info"]:
            if addr.get("temporary", False) is True:
                continue
            if "local" not in addr:
                continue
            if addr["local"].startswith("fc") or addr["local"].startswith("fd"):
                continue
            return addr["local"]

    raise NoIpError("no IP found")


def update_ip(current_ip, domain, username, password, url):
    try:
        response = requests.get(
            url,
            params={"hostname": domain, "myip": current_ip,},
            auth=(username, password),
        )
    except Exception as e:
        raise IpUpdateError("IP update failed: " + str(e))

    if "good" in response.text:
        logger.info(f"updated IP to: {current_ip}")
    elif "nochg" in response.text:
        logger.info(f"IP up to date: {current_ip}")
    else:
        raise IpUpdateError("IP update failed: " + response.text)


def main():
    parser = argparse.ArgumentParser(description="update ipv6",)
    parser.add_argument("--verbosity", "-v", type=int, choices=range(5), default=3)
    parser.add_argument("--config", type=Path, default=Path("config.ini"))

    args = parser.parse_args()

    logger.setLevel(
        [
            logging.CRITICAL,
            logging.ERROR,
            logging.WARNING,
            logging.INFO,
            logging.DEBUG,
        ][args.verbosity]
    )

    config_parser = ConfigParser()
    config_parser.read(args.config)
    config = config_parser[config_parser.sections()[0]]

    old_ip = None
    last_update = datetime(1970, 1, 1)
    while True:

        try:
            current_ip = get_ip(config["net_dev"])
        except NoIpError as e:
            logger.error(e)
            logger.error("sleeping for 1 minute")
            time.sleep(60)
            continue

        if current_ip != old_ip or datetime.now() >= (
            last_update + timedelta(hours=12)
        ):
            try:
                update_ip(
                    current_ip,
                    domain=config["domain"],
                    username=config["username"],
                    password=config["password"],
                    url=config["url"],
                )
            except IpUpdateError as e:
                logger.error(e)
                logger.error("sleeping for 10 minutes")
                time.sleep(10 * 60)
                continue
            old_ip = current_ip
            last_update = datetime.now()

        time.sleep(1)


if __name__ == "__main__":
    main()
