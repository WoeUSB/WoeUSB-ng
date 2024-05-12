#!/usr/bin/env python3

import os
import re
import subprocess


def usb_drive(show_all=False):
    devices_list = []

    lsblk = subprocess.run(["lsblk",
                            "--output", "NAME,SIZE,MODEL",
                            "--noheadings",
                            "--nodeps"], capture_output=True, text=True).stdout

    devices = re.sub("sr[0-9]|cdrom[0-9]", "", lsblk).split()

    for device in devices:
        if is_removable_and_writable_device(device):
            if not show_all:
                continue

        block_device = f"/dev/{device}"

        device_capacity = subprocess.run(["lsblk",
                                          "--output", "SIZE",
                                          "--noheadings",
                                          "--nodeps",
                                          block_device], capture_output=True, text=True).stdout.strip()

        device_model = subprocess.run(["lsblk",
                                       "--output", "MODEL",
                                       "--noheadings",
                                       "--nodeps",
                                       block_device], capture_output=True, text=True).stdout.strip()

        if device_model != "":
            devices_list.append([block_device, f"{block_device} ({device_model}, {device_capacity})"])
        else:
            devices_list.append([block_device, f"{block_device} ({device_capacity})"])

    return devices_list


def is_removable_and_writable_device(block_device_name):
    sysfs_block_device_dir = f"/sys/block/{block_device_name}"

    if os.path.exists(sysfs_block_device_dir):
        removable_path = os.path.join(sysfs_block_device_dir, "removable")
        ro_path = os.path.join(sysfs_block_device_dir, "ro")

        if os.path.isfile(removable_path) and os.path.isfile(ro_path):
            with open(removable_path) as removable, open(ro_path) as ro:
                removable_content = removable.read().strip()
                ro_content = ro.read().strip()

            return removable_content == "1" and ro_content == "0"

    return False


def dvd_drive():
    devices_list = []
    find = subprocess.run(["find", "/sys/block",
                           "-maxdepth", "1",
                           "-mindepth", "1"], capture_output=True, text=True).stdout.split()
    devices = [device for device in find if re.findall("sr[0-9]", device)]

    for device in devices:
        optical_disk_drive_devfs_path = f"/dev/{re.findall('sr[0-9]', device)[0]}"

        with open(os.path.join(device, "device/model"), "r") as model:
            model_content = model.read().strip()

        devices_list.append([optical_disk_drive_devfs_path, f"{optical_disk_drive_devfs_path} - {model_content}"])

    return devices_list
