import os
import subprocess
import time

import WoeUSB.utils as utils
import WoeUSB.miscellaneous as miscellaneous

_ = miscellaneous.i18n


def make_system_realize_partition_table_changed(target_device):
    """
    :param target_device:
    :return:
    """
    utils.print_with_color(_("Making system realize that partition table has changed..."))

    subprocess.run(["blockdev", "--rereadpt", target_device])
    utils.print_with_color(_("Wait 3 seconds for block device nodes to populate..."))

    time.sleep(3)


def buggy_motherboards_that_ignore_disks_without_boot_flag_toggled(target_device):
    """
    Some buggy BIOSes won't put detected device with valid MBR
    but no partitions with boot flag toggled into the boot menu,
    workaround this by setting the first partition's boot flag
    (which partition doesn't matter as GNU GRUB doesn't depend on it anyway)

    :param target_device:
    :return:
    """
    utils.print_with_color(
        _("Applying workaround for buggy motherboards that will ignore disks with no partitions with the boot flag toggled")
    )

    subprocess.run(["parted", "--script",
                    target_device,
                    "set", "1", "boot", "on"])


def support_windows_7_uefi_boot(source_fs_mountpoint, target_fs_mountpoint):
    """
    As Windows 7's installation media doesn't place the required EFI
    bootloaders in the right location, we extract them from the
    system image manually

    :TODO: Create Windows 7 checking

    :param source_fs_mountpoint:
    :param target_fs_mountpoint:
    :return:
    """
    grep = subprocess.run(["grep", "--extended-regexp", "--quiet", "^MinServer=7[0-9]{3}\.[0-9]",
                           source_fs_mountpoint + "/sources/cversion.ini"],
                          stdout=subprocess.PIPE).stdout.decode("utf-8").strip()
    if grep == "" and not os.path.isfile(source_fs_mountpoint + "/bootmgr.efi"):
        return 0

    utils.print_with_color(
        _("Source media seems to be Windows 7-based with EFI support, applying workaround to make it support UEFI booting"),
        "yellow")

    test_efi_directory = subprocess.run(["find", target_fs_mountpoint, "-ipath", target_fs_mountpoint + "/efi"],
                                        stdout=subprocess.PIPE).stdout.decode("utf-8").strip()

    if test_efi_directory == "":
        efi_directory = target_fs_mountpoint + "/efi"
        if utils.verbose:
            utils.print_with_color(_("DEBUG: Can't find efi directory, use {0}").format(efi_directory), "yellow")
    else:
        efi_directory = test_efi_directory
        if utils.verbose:
            utils.print_with_color(_("DEBUG: {0} detected.").format(efi_directory), "yellow")

    test_efi_boot_directory = subprocess.run(["find", target_fs_mountpoint, "-ipath", target_fs_mountpoint + "/boot"],
                                             stdout=subprocess.PIPE).stdout.decode("utf-8").strip()

    if test_efi_boot_directory == "":
        efi_boot_directory = target_fs_mountpoint + "/boot"
        if utils.verbose:
            utils.print_with_color(_("DEBUG: Can't find efi/boot directory, use {0}").format(efi_boot_directory), "yellow")
    else:
        efi_boot_directory = test_efi_boot_directory
        if utils.verbose:
            utils.print_with_color(_("DEBUG: {0} detected.").format(efi_boot_directory), "yellow")

    # If there's already an EFI bootloader existed, skip the workaround
    test_efi_bootloader = subprocess.run(
        ["find", target_fs_mountpoint, "-ipath", target_fs_mountpoint + "/efi/boot/boot*.efi"],
        stdout=subprocess.PIPE).stdout.decode("utf-8").strip()

    if test_efi_bootloader != "":
        utils.print_with_color(_("INFO: Detected existing EFI bootloader, workaround skipped."))
        return 0

    os.makedirs(efi_boot_directory, exist_ok=True)

    bootloader = subprocess.run(["7z",
                                 "e",
                                 "-so",
                                 source_fs_mountpoint + "/sources/install.wim",
                                 "Windows/Boot/EFI/bootmgfw.efi"], stdout=subprocess.PIPE).stdout

    with open(efi_boot_directory + "/bootx64.efi", "wb") as target_bootloader:
        target_bootloader.write(bootloader)
