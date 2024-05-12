#!/usr/bin/env python3

import os
import time
import shutil
import argparse
import tempfile
import traceback
import threading
import subprocess
import urllib.request
import urllib.error
from datetime import datetime

from WoeUSB import utils, workaround, miscellaneous

_ = miscellaneous.i18n

application_name = 'WoeUSB'
application_version = miscellaneous.__version__
DEFAULT_NEW_FS_LABEL = 'Windows USB'

application_site_url = 'https://github.com/slacka/WoeUSB'
application_copyright_declaration = "Copyright © Colin GILLE / congelli501 2013\\nCopyright © slacka et.al. 2017"
application_copyright_notice = application_name + " is free software licensed under the GNU General Public License version 3(or any later version of your preference) that gives you THE 4 ESSENTIAL FREEDOMS\\nhttps://www.gnu.org/philosophy/"

#: Increase verbosity, provide more information when required
verbose = False

debug = False

CopyFiles_handle = threading.Thread()

#: Execution state for cleanup functions to determine if clean up is required
current_state = 'pre-init'

gui = None


def init(from_cli=True, install_mode=None, source_media=None, target_media=None, workaround_bios_boot_flag=False,
         target_filesystem_type="FAT", filesystem_label=DEFAULT_NEW_FS_LABEL):
    """
    :param from_cli:
    :type from_cli: bool
    :param install_mode:
    :param source_media:
    :param target_media:
    :param workaround_bios_boot_flag:
    :param target_filesystem_type:
    :param filesystem_label:
    :return: List
    """
    source_fs_mountpoint = f"/media/woeusb_source_{round((datetime.today() - datetime.fromtimestamp(0)).total_seconds())}_{os.getpid()}"
    target_fs_mountpoint = f"/media/woeusb_target_{round((datetime.today() - datetime.fromtimestamp(0)).total_seconds())}_{os.getpid()}"

    temp_directory = tempfile.mkdtemp(prefix="WoeUSB.")

    verbose = False

    no_color = True

    debug = False

    parser = None

    if from_cli:
        parser = setup_arguments()
        args = parser.parse_args()

        if args.about:
            print_application_info()
            return 0

        if args.device:
            install_mode = "device"
        elif args.partition:
            install_mode = "partition"
        else:
            utils.print_with_color(_("You need to specify installation type (--device or --partition)"))
            return 1

        #: source_media may be an optical disk drive or a disk image
        source_media = args.source
        #: target_media may be an entire USB storage device or just a partition
        target_media = args.target

        workaround_bios_boot_flag = args.workaround_bios_boot_flag

        skip_legacy_bootloader = args.workaround_skip_grub

        target_filesystem_type = args.target_filesystem

        filesystem_label = args.label

        verbose = args.verbose

        no_color = args.no_color

        debug = args.debug

    utils.no_color = no_color
    utils.verbose = verbose
    utils.gui = gui

    if from_cli:
        return [source_fs_mountpoint, target_fs_mountpoint, temp_directory, install_mode, source_media, target_media,
                workaround_bios_boot_flag, skip_legacy_bootloader, target_filesystem_type, filesystem_label, verbose, debug, parser]
    else:
        return [source_fs_mountpoint, target_fs_mountpoint, temp_directory, target_media]


def main(source_fs_mountpoint, target_fs_mountpoint, source_media, target_media, install_mode, temp_directory,
         target_filesystem_type, workaround_bios_boot_flag, parser=None, skip_legacy_bootloader=False):
    """
    :param parser:
    :param source_fs_mountpoint:
    :param target_fs_mountpoint:
    :param source_media:
    :param target_media:
    :param install_mode:
    :param temp_directory:
    :param target_filesystem_type:
    :param workaround_bios_boot_flag:
    :return: 0 - success; 1 - failure
    """
    global debug
    global verbose
    global no_color
    global current_state
    global target_device

    current_state = 'enter-init'

    command_mkdosfs, command_mkntfs, command_grubinstall = utils.check_runtime_dependencies(application_name)
    if command_grubinstall == "grub-install":
        name_grub_prefix = "grub"
    else:
        name_grub_prefix = "grub2"

    utils.print_with_color(application_name + " v" + application_version)
    utils.print_with_color("==============================")

    if os.getuid() != 0:
        utils.print_with_color(_("Warning: You are not running {0} as root!").format(application_name), "yellow")
        utils.print_with_color(_("Warning: This might be the reason of the following failure."), "yellow")

    if utils.check_runtime_parameters(install_mode, source_media, target_media):
        parser.print_help()
        return 1

    target_device, target_partition = utils.determine_target_parameters(install_mode, target_media)

    if utils.check_source_and_target_not_busy(install_mode, source_media, target_device, target_partition):
        return 1

    current_state = "start-mounting"

    if mount_source_filesystem(source_media, source_fs_mountpoint):
        utils.print_with_color(_("Error: Unable to mount source filesystem"), "red")
        return 1

    if target_filesystem_type == "FAT":
        if utils.check_fat32_filesize_limitation(source_fs_mountpoint):
            target_filesystem_type = "NTFS"

    if install_mode == "device":
        wipe_existing_partition_table_and_filesystem_signatures(target_device)
        create_target_partition_table(target_device, "legacy")
        create_target_partition(target_device, target_partition, target_filesystem_type, target_filesystem_type,
                                command_mkdosfs,
                                command_mkntfs)

        if target_filesystem_type == "NTFS":
            create_uefi_ntfs_support_partition(target_device)
            install_uefi_ntfs_support_partition(target_device + "2", temp_directory)

    if install_mode == "partition":
        utils.check_target_partition(target_partition, target_device)
        utils.check_target_partition(target_partition, target_device)

    if mount_target_filesystem(target_partition, target_fs_mountpoint):
        utils.print_with_color(_("Error: Unable to mount target filesystem"), "red")
        return 1

    if workaround_bios_boot_flag and install_mode == "device":
        if apply_workaround_bios_boot_flag(source_fs_mountpoint, target_fs_mountpoint, target_device,
                                           target_partition, command_grubinstall, name_grub_prefix,
                                           skip_legacy_bootloader):
            utils.print_with_color(_("Error: Unable to apply workaround for BIOS boot flag"), "red")
            return 1

    current_state = "start-copying"

    if install_mode == "device":
        copy_files_thread = threading.Thread(target=copy_files, args=(source_fs_mountpoint, target_fs_mountpoint,))
        copy_files_thread.start()

        if debug:
            print(_("Started copy files thread. Waiting until it finishes..."))
        if gui:
            gui.toggle_button()
            utils.print_with_color(
                _("Info: Writing in progress, do not remove the media until the process is complete."),
                "yellow")

        while copy_files_thread.is_alive():
            time.sleep(1)
            if debug:
                print(".", end="", flush=True)

        copy_files_thread.join()

        if gui:
            gui.toggle_button()

        if debug:
            print()
            print(_("Copying finished"))

        if CopyFiles_handle.is_alive():
            utils.print_with_color(_("Error: Copying process failed."), "red")
            return 1

        if os.system("sync") != 0:
            utils.print_with_color(_("Warning: Synchronization before unmounting failed."), "yellow")
    else:
        copy_files(source_fs_mountpoint, target_fs_mountpoint)

    current_state = "start-unmounting"

    if unmount_target_filesystem(target_fs_mountpoint):
        utils.print_with_color(_("Error: Unable to unmount target filesystem"), "red")
        return 1

    if unmount_source_filesystem(source_fs_mountpoint):
        utils.print_with_color(_("Error: Unable to unmount source filesystem"), "red")
        return 1

    if install_mode == "device":
        if update_partition_info(target_device, target_partition):
            utils.print_with_color(_("Error: Unable to update partition info"), "red")
            return 1

    if install_mode == "device":
        utils.print_with_color(_("The target device has been successfully prepared"), "green")
    else:
        utils.print_with_color(_("The target partition has been successfully prepared"), "green")

    return 0


def mount_source_filesystem(source_media, source_fs_mountpoint):
    """
    :param source_media:
    :param source_fs_mountpoint:
    :return: 0 - success; 1 - failure
    """
    try:
        utils.mount(source_media, source_fs_mountpoint)
        return 0
    except Exception as e:
        utils.print_with_color(str(e), "red")
        return 1


def mount_target_filesystem(target_partition, target_fs_mountpoint):
    """
    :param target_partition:
    :param target_fs_mountpoint:
    :return: 0 - success; 1 - failure
    """
    try:
        utils.mount(target_partition, target_fs_mountpoint)
        return 0
    except Exception as e:
        utils.print_with_color(str(e), "red")
        return 1


def unmount_source_filesystem(source_fs_mountpoint):
    """
    :param source_fs_mountpoint:
    :return: 0 - success; 1 - failure
    """
    try:
        utils.unmount(source_fs_mountpoint)
        return 0
    except Exception as e:
        utils.print_with_color(str(e), "red")
        return 1


def unmount_target_filesystem(target_fs_mountpoint):
    """
    :param target_fs_mountpoint:
    :return: 0 - success; 1 - failure
    """
    try:
        utils.unmount(target_fs_mountpoint)
        return 0
    except Exception as e:
        utils.print_with_color(str(e), "red")
        return 1


def wipe_existing_partition_table_and_filesystem_signatures(target_device):
    """
    :param target_device:
    :return: 0 - success; 1 - failure
    """
    try:
        utils.wipe_target_device(target_device)
        return 0
    except Exception as e:
        utils.print_with_color(str(e), "red")
        return 1


def create_target_partition_table(target_device, target_partition_table_type):
    """
    :param target_device:
    :param target_partition_table_type:
    :return: 0 - success; 1 - failure
    """
    try:
        utils.create_partition_table(target_device, target_partition_table_type)
        return 0
    except Exception as e:
        utils.print_with_color(str(e), "red")
        return 1


def create_target_partition(target_device, target_partition, target_filesystem_type, filesystem_label,
                            command_mkdosfs, command_mkntfs):
    """
    :param target_device:
    :param target_partition:
    :param target_filesystem_type:
    :param filesystem_label:
    :param command_mkdosfs:
    :param command_mkntfs:
    :return: 0 - success; 1 - failure
    """
    try:
        utils.create_partition(target_device, target_partition, target_filesystem_type, filesystem_label,
                               command_mkdosfs, command_mkntfs)
        return 0
    except Exception as e:
        utils.print_with_color(str(e), "red")
        return 1


def create_uefi_ntfs_support_partition(target_device):
    """
    :param target_device:
    :return: 0 - success; 1 - failure
    """
    try:
        utils.create_uefi_ntfs_support_partition(target_device)
        return 0
    except Exception as e:
        utils.print_with_color(str(e), "red")
        return 1


def install_uefi_ntfs_support_partition(target_device, temp_directory):
    """
    :param target_device:
    :param temp_directory:
    :return: 0 - success; 1 - failure
    """
    try:
        utils.install_uefi_ntfs_support_partition(target_device, temp_directory)
        return 0
    except Exception as e:
        utils.print_with_color(str(e), "red")
        return 1


def apply_workaround_bios_boot_flag(source_fs_mountpoint, target_fs_mountpoint, target_device, target_partition,
                                   command_grubinstall, name_grub_prefix, skip_legacy_bootloader):
    """
    :param source_fs_mountpoint:
    :param target_fs_mountpoint:
    :param target_device:
    :param target_partition:
    :param command_grubinstall:
    :param name_grub_prefix:
    :param skip_legacy_bootloader:
    :return: 0 - success; 1 - failure
    """
    try:
        workaround.apply_bios_boot_flag_workaround(source_fs_mountpoint, target_fs_mountpoint, target_device,
                                                   target_partition,
                                                   command_grubinstall, name_grub_prefix, skip_legacy_bootloader)
        return 0
    except Exception as e:
        utils.print_with_color(str(e), "red")
        return 1


def copy_files(source_fs_mountpoint, target_fs_mountpoint):
    """
    :param source_fs_mountpoint:
    :param target_fs_mountpoint:
    :return: 0 - success; 1 - failure
    """
    try:
        utils.copy_files(source_fs_mountpoint, target_fs_mountpoint)
        return 0
    except Exception as e:
        utils.print_with_color(str(e), "red")
        return 1


def update_partition_info(target_device, target_partition):
    """
    :param target_device:
    :param target_partition:
    :return: 0 - success; 1 - failure
    """
    try:
        utils.update_partition_info(target_device, target_partition)
        return 0
    except Exception as e:
        utils.print_with_color(str(e), "red")
        return 1


def check_target_partition(target_device, target_partition):
    """
    :param target_device:
    :param target_partition:
    :return: 0 - success; 1 - failure
    """
    try:
        return utils.check_target_partition(target_device, target_partition)
    except Exception as e:
        utils.print_with_color(str(e), "red")
        return 1
