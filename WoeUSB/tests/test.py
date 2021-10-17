import os

import pytest

import WoeUSB.utils
from mocks import mock_os


@pytest.mark.parametrize(
    "size, output",
    [
        (2 ** 16, 0),
        (2 ** 32, 1)
    ]
)
class TestCheckFat32FilesizeLimitation:
    def test_size_ok(self, size, output, monkeypatch):
        mock_os.size_of_file_two = size

        monkeypatch.setattr(os, "walk", mock_os.walk)
        monkeypatch.setattr(os.path, "getsize", mock_os.getsize)

        result = WoeUSB.utils.check_fat32_filesize_limitation("../")
        assert result == output
