#!/usr/bin/env python3
import os

from dotenv import load_dotenv
from ruamel.yaml import YAML
from spice_bot import SpiceBot

def main():
    load_dotenv("../.env")
    yaml = YAML()
    with open('../config.yaml') as fp:
        config = yaml.load(fp)
    TOKEN = os.getenv("DISCORD_TOKEN")
    client = SpiceBot(config)
    client.run(TOKEN)

if __name__ == '__main__':
    main()
