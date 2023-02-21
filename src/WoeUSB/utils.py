import os
import pathlib
import re
import shutil
import subprocess
import sys
from xml.dom.minidom import parseString

import WoeUSB.miscellaneous as miscellaneous

_ = miscellaneous.i18n

#: Disable message coloring when set to True, set by --no-color
no_color = False

# External tools
try:
    import termcolor
except ImportError:
    print("Module termcolor is not installed, text coloring disabled")
    no_color = True

gui = None
verbose = False


def check_runtime_dependencies(application_name):
    """
    :param application_name:
    :return:
    """
    result = "success"

    system_commands = ["mount", "umount", "wipefs", "lsblk", "blockdev", "df", "parted", "7z"]
    for command in system_commands:
        if shutil.which(command) is None:
            print_with_color(
                _("Error: {0} requires {1} command in the executable search path, but it is not found.").format(
                    application_name, command),
                "red")
            result = "failed"

    fat = ["mkdosfs", "mkfs.msdos", "mkfs.vfat", "mkfs.fat"]
    for command in fat:
        if shutil.which(command) is not None:
            fat = command
            break

    if isinstance(fat, list):
        print_with_color(_("Error: mkdosfs/mkfs.msdos/mkfs.vfat/mkfs.fat command not found!"), "red")
        print_with_color(_("Error: Please make sure that dosfstools is properly installed!"), "red")
        result = "failed"

    ntfs = "mkntfs"
    if shutil.which("mkntfs") is None:
        print_with_color(_("Error: mkntfs command not found!"), "red")
        print_with_color(_("Error: Please make sure that ntfs-3g is properly installed!"), "red")
        result = "failed"

    grub = ["grub-install", "grub2-install"]
    for command in grub:
        if shutil.which(command) is not None:
            grub = command
            break

    if isinstance(grub, list):
        print_with_color(_("Error: grub-install or grub2-install command not found!"), "red")
        print_with_color(_("Error: Please make sure that GNU GRUB is properly installed!"), "red")
        result = "failed"

    if result != "success":
        raise RuntimeError("Dependencies are not met")
    else:
        return [fat, ntfs, grub]


def check_runtime_parameters(install_mode, source_media, target_media):
    """
    :param install_mode:
    :param source_media:
    :param target_media:
    :return:
    """
    if not os.path.isfile(source_media) and not pathlib.Path(source_media).is_block_device():
        print_with_color(
            _("Error: Source media \"{0}\" not found or not a regular file or a block device file!").format(
                source_media),
            "red")
        return 1

    if not pathlib.Path(target_media).is_block_device():
        print_with_color(_("Error: Target media \"{0}\" is not a block device file!").format(target_media), "red")
        return 1

    if install_mode == "device" and target_media[-1].isdigit():
        print_with_color(_("Error: Target media \"{0}\" is not an entire storage device!").format(target_media), "red")
        return 1

    if install_mode == "partition" and not target_media[-1].isdigit():
        print_with_color(_("Error: Target media \"{0}\" is not an partition!").format(target_media), "red")
        return 1
    return 0


def determine_target_parameters(install_mode, target_media):
    """
    :param install_mode:
    :param target_media:
    :return:
    """
    if install_mode == "partition":
        target_partition = target_media

        while target_media[-1].isdigit():
            target_media = target_media[:-1]
        target_device = target_media
    else:
        target_device = target_media
        target_partition = target_media + str(1)

    if verbose:
        print_with_color(_("Info: Target device is {0}").format(target_device))
        print_with_color(_("Info: Target partition is {0}").format(target_partition))

    return [target_device, target_partition]


def check_is_target_device_busy(device):
    """
    :param device:
    :return:
    """
    mount = subprocess.run("mount", stdout=subprocess.PIPE).stdout.decode("utf-8").strip()
    if re.findall(device, mount) != []:
        mounts = re.findall(rf'{device}\S*', mount)
        print_with_color(_("Warning: The following partitions will be unmounted: {0}").format(mounts), "yellow")
        for partition in mounts:
            if subprocess.run(["umount", partition]).returncode:
                return 1
    return 0


def check_source_and_target_not_busy(install_mode, source_media, target_device, target_partition):
    """
    :param install_mode:
    :param source_media:
    :param target_device:
    :param target_partition:
    :return:
    """
    if check_is_target_device_busy(source_media):
        print_with_color(_("Error: Source media is currently mounted, unmount the partition then try again"), "red")
        return 1

    if install_mode == "partition":
        if check_is_target_device_busy(target_partition):
            print_with_color(_("Error: Target partition is currently mounted, unmount the partition then try again"),
                             "red")
            return 1
    else:
        if check_is_target_device_busy(target_device):
            print_with_color(
                _(
                    "Error: Target device is currently busy, unmount all mounted partitions in target device then try again"),
                "red")
            return 1


def check_fat32_filesize_limitation(source_fs_mountpoint):
    """
    :param source_fs_mountpoint:
    :return:
    """
    for dirpath, dirnames, filenames in os.walk(source_fs_mountpoint):
        for file in filenames:
            path = os.path.join(dirpath, file)
            if os.path.getsize(path) > (2 ** 32) - 1:  # Max fat32 file size
                print_with_color(
                    _(
                        "Warning: File {0} in source image has exceed the FAT32 Filesystem 4GiB Single File Size Limitation, swiching to NTFS filesystem.").format(
                        path),
                    "yellow")
                print_with_color(
                    _(
                        "Refer: https://github.com/slacka/WoeUSB/wiki/Limitations#fat32-filesystem-4gib-single-file-size-limitation for more info."),
                    "yellow")
                return 1
    return 0


def check_target_partition(target_partition, target_device):
    """
    Check target partition for potential problems before mounting them for --partition creation mode as we don't know about the existing partition

    :param target_partition: The target partition to check
    :param target_device: The parent device of the target partition, this is passed in to check UEFI:NTFS filesystem's existence on check_uefi_ntfs_support_partition
    :return:
    """
    target_filesystem = subprocess.run(["lsblk",
                                        "--output", "FSTYPE",
                                        "--noheadings",
                                        target_partition], stdout=subprocess.PIPE).stdout.decode("utf-8").strip()

    if target_filesystem == "vfat":
        pass  # supported
    elif target_filesystem == "ntfs":
        check_uefi_ntfs_support_partition(target_device)
    else:
        print_with_color(_("Error: Target filesystem not supported, currently supported filesystem: FAT, NTFS."), "red")
        return 1

    return 0


def check_uefi_ntfs_support_partition(target_device):
    """
    Check if the UEFI:NTFS support partition exists
    Currently it depends on the fact that this partition has a label of "UEFI_NTFS"

    :param target_device: The UEFI:NTFS partition residing entier device file
    :return:
    """
    lsblk = subprocess.run(["lsblk",
                            "--output", "LABEL",
                            "--noheadings",
                            target_device], stdout=subprocess.PIPE).stdout.decode("utf-8").strip()

    if re.findall("UEFI_NTFS", lsblk) != []:
        print_with_color(
            _("Warning: Your device doesn't seems to have an UEFI:NTFS partition, "
              "UEFI booting will fail if the motherboard firmware itself doesn't support NTFS filesystem!"))
        print_with_color(
            _("Info: You may recreate disk with an UEFI:NTFS partition by using the --device creation method"))


def check_target_filesystem_free_space(target_fs_mountpoint, source_fs_mountpoint, target_partition):
    """
    :param target_fs_mountpoint:
    :param source_fs_mountpoint:
    :param target_partition:
    :return:
    """
    df = subprocess.run(["df",
                         "--block-size=1",
                         target_fs_mountpoint], stdout=subprocess.PIPE).stdout
    # free_space = int(df.strip().split()[4])

    awk = subprocess.Popen(["awk", "{print $4}"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    free_space = awk.communicate(input=df)[0]
    free_space = free_space.decode("utf-8").strip()
    free_space = re.sub("[^0-9]", "", free_space)
    free_space = int(free_space)

    needed_space = 0
    for dirpath, dirnames, filenames in os.walk(source_fs_mountpoint):
        for file in filenames:
            path = os.path.join(dirpath, file)
            needed_space += os.path.getsize(path)

    additional_space_required_for_grub_installation = 1000 * 1000 * 10  # 10MiB

    needed_space += additional_space_required_for_grub_installation

    if needed_space > free_space:
        print_with_color(_("Error: Not enough free space on target partition!"))
        print_with_color(
            _("Error: We required {0}({1} bytes) but '{2}' only has {3}({4} bytes).")
            .format(
                str(get_size(str(needed_space))),
                str(needed_space),
                target_partition,
                str(free_space),
                str(free_space)))
        return 1


def print_with_color(text, color=""):
    """
    Print function
    This function takes into account no_color flag
    Also if used by gui, sends information to it, rather than putting it into standard output

    :param text: Text to be printed
    :param color: Color of the text
    """
    if gui is not None:
        gui.state = text
        if color == "red":
            gui.error = text
            sys.exit()
    else:
        if no_color or color == "":
            sys.stdout.write(text + "\n")
        else:
            termcolor.cprint(text, color)


def convert_to_human_readable_format(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Ti', suffix)


def get_size(path):
    total_size = 0
    for dirpath, __, filenames in os.walk(path):
        for file in filenames:
            path = os.path.join(dirpath, file)
            total_size += os.path.getsize(path)
    return total_size


def check_kill_signal():
    """
    Ok, you may asking yourself, what the f**k is this, and why is it called everywhere. Let me explain
    In python you can't just stop or kill thread, it must end its execution,
    or recognize moment where you want it to stop and politely perform euthanasia on itself.
    So, here, if gui is set, we throw exception which is going to be (hopefully) catch by GUI,
    simultaneously ending whatever script was doing meantime!
    Everyone goes to home happy and user is left with wrecked pendrive (just joking, next thing called by gui is cleanup)
    """
    if gui is not None:
        if gui.kill:
            raise sys.exit()


# noinspection DuplicatedCode
def update_policy_to_allow_for_running_gui_as_root(path):
    dom = parseString(
        "<?xml version=\"1.0\" ?>"
        "<!DOCTYPE policyconfig  PUBLIC '-//freedesktop//DTD polkit Policy Configuration 1.0//EN'  "
        "'http://www.freedesktop.org/software/polkit/policyconfig-1.dtd'><!-- \n"
        "DOC: https://www.freedesktop.org/software/polkit/docs/latest/polkit.8.html\n"
        "--><policyconfig>\n"
        "	<vendor>The WoeUSB Project</vendor>\n"
        "	<vendor_url>https://github.com/slacka/WoeUSB</vendor_url>\n"
        "	<icon_name>woeusbgui-icon</icon_name>\n"
        "\n"
        "	<action id=\"com.github.slacka.woeusb.run-gui-using-pkexec\">\n"
        "		<description>Run `woeusb` as SuperUser</description>\n"
        "		<description xml:lang=\"zh_TW\">以超級使用者(SuperUser)身份執行 `woeusb`</description>\n"
        "		<description xml:lang=\"pl_PL\">Uruchom `woeusb` jako root</description>\n"
        "		\n"
        "		<message>Authentication is required to run `woeusb` as SuperUser.</message>\n"
        "		<message xml:lang=\"zh_TW\">以超級使用者(SuperUser)身份執行 `woeusb` 需要通過身份驗證。</message>\n"
        "		<message xml:lang=\"pl_PL\">Wymagana jest autoryzacja do uruchomienia `woeusb` jako root</message>\n"
        "		\n"
        "		<defaults>\n"
        "			<allow_any>auth_admin</allow_any>\n"
        "			<allow_inactive>auth_admin</allow_inactive>\n"
        "			<allow_active>auth_admin_keep</allow_active>\n"
        "		</defaults>\n"
        "		\n"
        "		<annotate key=\"org.freedesktop.policykit.exec.path\">/usr/local/bin/woeusbgui</annotate>\n"
        "   		<annotate key=\"org.freedesktop.policykit.exec.allow_gui\">true</annotate>\n"
        "	</action>\n"
        "	<action id=\"com.github.slacka.woeusb.run-gui-using-pkexec-local\">\n"
        "		<description>Run `woeusb` as SuperUser</description>\n"
        "		<description xml:lang=\"zh_TW\">以超級使用者(SuperUser)身份執行 `woeusb`</description>\n"
        "		<description xml:lang=\"pl_PL\">Uruchom `woeusb` jako root</description>\n"
        "\n"
        "		<message>Authentication is required to run `woeusb` as SuperUser.</message>\n"
        "		<message xml:lang=\"zh_TW\">以超級使用者(SuperUser)身份執行 `woeusb` 需要通過身份驗證。</message>\n"
        "		<message xml:lang=\"pl_PL\">Wymagana jest autoryzacja do uruchomienia `woeusb` jako root</message>\n"
        "\n"
        "		<defaults>\n"
        "			<allow_any>auth_admin</allow_any>\n"
        "			<allow_inactive>auth_admin</allow_inactive>\n"
        "			<allow_active>auth_admin_keep</allow_active>\n"
        "		</defaults>\n"
        "\n"
        "		<annotate key=\"org.freedesktop.policykit.exec.path\">/usr/local/bin/woeusbgui</annotate>\n"
        "   		<annotate key=\"org.freedesktop.policykit.exec.allow_gui\">true</annotate>\n"
        "	</action>\n"
        "</policyconfig>"
    )
    for action in dom.getElementsByTagName('action'):
        if action.getAttribute('id') == "com.github.slacka.woeusb.run-gui-using-pkexec":
            for annotate in action.getElementsByTagName('annotate'):
                if annotate.getAttribute('key') == "org.freedesktop.policykit.exec.path":
                    annotate.childNodes[0].nodeValue = path

    with open("/usr/share/polkit-1/actions/com.github.woeusb.woeusb-ng.policy", "w") as file:
        file.write(dom.toxml())
