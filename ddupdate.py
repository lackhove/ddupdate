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
    current_ip = None
    for dev in reply:
        for addr in dev["addr_info"]:
            if addr.get("temporary", False) is True:
                continue
            if addr["local"].startswith("fc") or addr["local"].startswith("fd"):
                continue
            return addr["local"]

    raise NoIpError("no IP found")


def update_ip(current_ip, old_ip, domain, password, template=None):
    template = (
        template
        if template is not None
        else "https://dyndns.strato.com/nic/update?hostname={domain}&myip={current_ip}"
    )
    command = [
        "curl",
        "--silent",
        "--show-error",
        "--user",
        f"{domain}:{password}",
        template.format(domain=domain, current_ip=current_ip, password=password),
    ]
    proc = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8",
    )
    reply = proc.stdout + proc.stderr

    if proc.returncode != 0:
        raise IpUpdateError("IP update failed: " + reply)

    if "good" in reply:
        logger.info(f"updated IP to: {current_ip}")
    elif "nochg" in reply:
        logger.info(f"IP up to date: {current_ip}")
    else:
        raise IpUpdateError("IP update failed: " + reply)


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

    config = ConfigParser()
    config.read(args.config)
    default_section = config["DEFAULT"]

    old_ip = None
    last_update = datetime(1970, 1, 1)
    while True:

        try:
            current_ip = get_ip(default_section["net_dev"])
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
                    old_ip,
                    domain=default_section["domain"],
                    password=default_section["password"],
                    template=default_section.get("template", None),
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
