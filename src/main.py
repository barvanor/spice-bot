#!/usr/bin/env python3
import os
import logging

from dotenv import load_dotenv
from ruamel.yaml import YAML
from spice_bot import SpiceBot

def main():
    logging.basicConfig(level=logging.INFO)

    script_dir = os.path.dirname(__file__)
    env_path = os.path.join(script_dir, '../.env')
    config_path = os.path.join(script_dir, '../config.yaml')
    load_dotenv(env_path)
    yaml = YAML()
    with open(config_path) as fp:
        config = yaml.load(fp)
    TOKEN = os.getenv("DISCORD_TOKEN")
    client = SpiceBot(config)
    client.run(TOKEN)

if __name__ == '__main__':
    main()
