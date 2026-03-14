import argparse
import getpass
import json
import os
import sys

# Add parent directory to sys.path to allow imports from custom_components
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from custom_components.dreame_mower.dreame.cloud.cloud_device import DreameMowerCloudDevice

def main():
    parser = argparse.ArgumentParser(description="List Dreame devices for your account")
    parser.add_argument("--username", default=None, help="Cloud username (email); prompted if omitted")
    parser.add_argument("--country", default=None, help="Cloud country code (e.g. 'cn', 'eu'); default: eu")
    args = parser.parse_args()

    if args.username is None:
        args.username = input("Username (email): ")
    args.password = getpass.getpass("Password: ")
    if args.country is None:
        args.country = "eu"

    # Create DreameMowerCloudDevice with minimal info
    protocol = DreameMowerCloudDevice(
        username=args.username,
        password=args.password,
        country=args.country,
        account_type="dreame",  # Default to dreame account type
        device_id=""  # Empty device_id for listing devices
    )

    protocol._cloud_base.connect()
    devices = protocol._cloud_base.get_devices()
    print(json.dumps(devices, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
