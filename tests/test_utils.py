import os
import sys
import shutil
import pathlib

import pytest

sys.path.append(".")
import WoeUSB.utils


class TestCheckRuntimeDependencies:
    _system_commands = ["mount", "umount", "wipefs", "lsblk", "blockdev", "df", "parted", "7z"]
    _fat = ["mkdosfs", "mkfs.msdos", "mkfs.vfat", "mkfs.fat"]
    _ntfs = ["mkntfs"]
    _grub = ["grub-install", "grub2-install"]

    system_commands = []
    fat = []
    ntfs = []
    grub = []

    @pytest.fixture()
    def setup(self, monkeypatch):
        self.system_commands = self._system_commands.copy()
        self.fat = self._fat.copy()
        self.grub = self._grub.copy()
        self.ntfs = self._ntfs.copy()

        monkeypatch.setattr(shutil, "which", self.which)
        yield "setup"

    def which(self, command):
        if command in self.system_commands:
            return "./"
        elif command in self.fat:
            return "./"
        elif command in self.ntfs:
            return "./"
        elif command in self.grub:
            return "./"
        else:
            return None

    def test_success_on_correct_list(self, setup):
        WoeUSB.utils.check_runtime_dependencies("WoeUSB-ng")

    @pytest.mark.parametrize(
        "command",
        _system_commands
    )
    def test_fail_on_missing_system_command(self, command, setup):
        self.system_commands.remove(command)

        with pytest.raises(RuntimeError):
            WoeUSB.utils.check_runtime_dependencies("WoeUSB-ng")

    def test_fail_on_missing_fat_command(self, setup):
        self.fat = []

        with pytest.raises(RuntimeError):
            WoeUSB.utils.check_runtime_dependencies("WoeUSB-ng")

    @pytest.mark.parametrize(
        "command",
        _fat
    )
    def test_success_on_any_fat_command(self, command, setup):
        self.fat = [command]

        [fat, ntfs, grub] = WoeUSB.utils.check_runtime_dependencies("WoeUSB-ng")

        assert fat == command

    def test_fail_on_missing_ntfs_command(self, setup):
        self.ntfs = []

        with pytest.raises(RuntimeError):
            WoeUSB.utils.check_runtime_dependencies("WoeUSB-ng")

    @pytest.mark.parametrize(
        "command",
        _ntfs
    )
    def test_success_on_ntfs_command(self, command, setup):
        self.ntfs = [command]

        [fat, ntfs, grub] = WoeUSB.utils.check_runtime_dependencies("WoeUSB-ng")

        assert ntfs == command

    def test_fail_on_missing_grub_command(self, setup):
        self.grub = []

        with pytest.raises(RuntimeError):
            WoeUSB.utils.check_runtime_dependencies("WoeUSB-ng")

    @pytest.mark.parametrize(
        "command",
        _grub
    )
    def test_success_on_any_grub_command(self, command, setup):
        self.grub = [command]

        [fat, ntfs, grub] = WoeUSB.utils.check_runtime_dependencies("WoeUSB-ng")

        assert grub == command


class TestCheckRuntimeParameters:
    path_preserve = None
    it_is_a_file = ""
    it_is_a_block_device = []

    class Path:
        path = ""
        it_is_a_block_device = ""

        def __init__(self, path):
            self.path = path

        def is_block_device(self):
            return self.path in self.it_is_a_block_device

    @pytest.fixture()
    def setup(self, monkeypatch):
        monkeypatch.setattr(os.path, "isfile", self.isfile)
        self.path_preserve = pathlib.Path
        monkeypatch.setattr(pathlib, "Path", self.path)
        yield "setup"

    def isfile(self, path):
        return self.it_is_a_file == path

    def path(self, path):
        p = self.Path(path)
        p.it_is_a_block_device = self.it_is_a_block_device
        return p

    def test_source_media_is_a_file(self, setup):
        self.it_is_a_file = "./aFile.iso"
        self.it_is_a_block_device = ["/dev/my_dev"]

        result = WoeUSB.utils.check_runtime_parameters("device", "./aFile.iso", "/dev/my_dev")
        pathlib.Path = self.path_preserve
        assert result == 0

    def test_source_media_is_a_block_device(self, setup):
        self.it_is_a_file = ""
        self.it_is_a_block_device = ["/dev/my_source", "/dev/my_dev"]

        result = WoeUSB.utils.check_runtime_parameters("device", "/dev/my_source", "/dev/my_dev")
        pathlib.Path = self.path_preserve
        assert result == 0

    def test_source_media_doesnt_exist(self, setup):
        self.it_is_a_file = "./aFile.iso"
        self.it_is_a_block_device = ["/dev/my_dev"]

        result = WoeUSB.utils.check_runtime_parameters("device", "./aFile2.iso", "/dev/my_dev")
        pathlib.Path = self.path_preserve
        assert result == 1

    def test_target_media_is_a_file(self, setup):
        self.it_is_a_file = "./aFile.iso"
        self.it_is_a_block_device = ["/dev/my_dev"]

        result = WoeUSB.utils.check_runtime_parameters("device", "./aFile.iso", "./aFile.iso")
        pathlib.Path = self.path_preserve
        assert result == 1

    def test_device_mode_target_media_isnt_whole_device(self, setup):
        self.it_is_a_file = "./aFile.iso"
        self.it_is_a_block_device = ["/dev/my_dev1"]

        result = WoeUSB.utils.check_runtime_parameters("device", "./aFile.iso", "/dev/my_dev1")
        pathlib.Path = self.path_preserve
        assert result == 1

    def test_partition_mode_target_media_is_whole_device(self, setup):
        self.it_is_a_file = "./aFile.iso"
        self.it_is_a_block_device = ["/dev/my_dev"]

        result = WoeUSB.utils.check_runtime_parameters("partition", "./aFile.iso", "/dev/my_dev")
        pathlib.Path = self.path_preserve
        assert result == 1

    def test_partition_mode_target_media_isnt_whole_device(self, setup):
        self.it_is_a_file = "./aFile.iso"
        self.it_is_a_block_device = ["/dev/my_dev1"]

        result = WoeUSB.utils.check_runtime_parameters("partition", "./aFile.iso", "/dev/my_dev1")
        pathlib.Path = self.path_preserve
        assert result == 0


class TestDetermineTargetParameters:
    def test_device(self):
        [target_device, target_partition] = WoeUSB.utils.determine_target_parameters("device", "/dev/sda")
        assert {target_device, target_partition} \
               .difference(["/dev/sda", "/dev/sda1"]) == set()

    def test_partition(self):
        [target_device, target_partition] = WoeUSB.utils.determine_target_parameters("partition", "/dev/sda1")
        assert {target_device, target_partition} \
               .difference(["/dev/sda", "/dev/sda1"]) == set()


class TestCheckFat32FilesizeLimitation:
    @pytest.fixture()
    def setup(self, monkeypatch):
        monkeypatch.setattr(os, "walk", self.walk)
        monkeypatch.setattr(os.path, "getsize", self.getsize)
        yield "setup"

    size_of_file_two = 10

    @staticmethod
    def walk(path):
        dirpath = "/test/"
        dirnames = ["dir_one", "dir_two"]
        filenames = ["file_one", "file_two", "file_three"]
        yield dirpath, dirnames, filenames

    def getsize(self, path):
        if path == "/test/file_two":
            return self.size_of_file_two
        else:
            return 10

    @pytest.mark.parametrize(
        "size, output",
        [
            (2 ** 16, 0),
            (2 ** (32 - 1), 0),
            (2 ** 32, 1)
        ]
    )
    def test_size(self, size, output, setup):
        self.size_of_file_two = size

        result = WoeUSB.utils.check_fat32_filesize_limitation("../")
        assert result == output
