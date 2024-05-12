import os
import subprocess
import time
import logging
import WoeUSB.utils as utils
import WoeUSB.miscellaneous as miscellaneous

_ = miscellaneous.i18n

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def make_system_realize_partition_table_changed(target_device):
    """
    Updates the system to recognize changes in the partition table.
    :param target_device: The target device.
    """
    logger.info(_("Making the system realize that the partition table has changed..."))
    subprocess.run(["blockdev", "--rereadpt", target_device], check=True)
    logger.info(_("Waiting 3 seconds for block device nodes to populate..."))
    time.sleep(3)


def buggy_motherboards_that_ignore_disks_without_boot_flag_toggled(target_device):
    """
    Applies workaround for buggy motherboards ignoring disks without boot flag toggled.
    :param target_device: The target device.
    """
    logger.info(_("Applying workaround for buggy motherboards..."))
    subprocess.run(["parted", "--script", target_device, "set", "1", "boot", "on"], check=True)


def support_windows_7_uefi_boot(source_fs_mountpoint, target_fs_mountpoint):
    """
    Supports UEFI boot for Windows 7 installation media.
    :param source_fs_mountpoint: Source filesystem mount point.
    :param target_fs_mountpoint: Target filesystem mount point.
    """
    logger.info(_("Supporting Windows 7 UEFI boot..."))
    cversion_file = os.path.join(source_fs_mountpoint, "sources", "cversion.ini")
    bootmgr_efi = os.path.join(source_fs_mountpoint, "bootmgr.efi")

    if os.path.exists(cversion_file) and os.path.exists(bootmgr_efi):
        logger.warning(_("Source media seems to be Windows 7-based with EFI support."))
        efi_directory = os.path.join(target_fs_mountpoint, "efi")
        efi_boot_directory = os.path.join(target_fs_mountpoint, "boot")
        os.makedirs(efi_boot_directory, exist_ok=True)

        # Check if an EFI bootloader already exists
        efi_bootloader = os.path.join(efi_directory, "boot", "boot*.efi")
        if not glob.glob(efi_bootloader):
            logger.info(_("No existing EFI bootloader detected. Applying workaround..."))

            # Extract Windows 7 EFI bootloader
            bootmgfw_efi = subprocess.run(
                ["7z", "e", "-so", os.path.join(source_fs_mountpoint, "sources", "install.wim"),
                 "Windows/Boot/EFI/bootmgfw.efi"], stdout=subprocess.PIPE, check=True).stdout

            # Write bootloader to target boot directory
            with open(os.path.join(efi_boot_directory, "bootx64.efi"), "wb") as target_bootloader:
                target_bootloader.write(bootmgfw_efi)
    else:
        logger.info(_("Windows 7 UEFI boot not supported for this media."))

