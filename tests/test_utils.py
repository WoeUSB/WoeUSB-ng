import os
import shutil
import sys

import pytest

from mocks import mock_os

sys.path.append(".")
import WoeUSB.utils


class TestDetermineTargetParameters:
    def test_device(self):
        [target_device, target_partition] = WoeUSB.utils.determine_target_parameters("device", "/dev/sda")
        assert {target_device, target_partition} \
               .difference(["/dev/sda", "/dev/sda1"]) == set()

    def test_partition(self):
        [target_device, target_partition] = WoeUSB.utils.determine_target_parameters("partition", "/dev/sda1")
        assert {target_device, target_partition} \
               .difference(["/dev/sda", "/dev/sda1"]) == set()


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


class TestCheckFat32FilesizeLimitation:
    @staticmethod
    @pytest.fixture()
    def setup(monkeypatch):
        monkeypatch.setattr(os, "walk", mock_os.walk)
        monkeypatch.setattr(os.path, "getsize", mock_os.getsize)
        yield "setup"

    @pytest.mark.parametrize(
        "size, output",
        [
            (2 ** 16, 0),
            (2 ** (32 - 1), 0),
            (2 ** 32, 1)
        ]
    )
    def test_size(self, size, output, setup):
        mock_os.size_of_file_two = size

        result = WoeUSB.utils.check_fat32_filesize_limitation("../")
        assert result == output
