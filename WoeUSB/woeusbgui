#!/usr/bin/env python3

"""
A Linux program to create bootable Windows USB stick from a real Windows DVD or an image
Copyright © 2013 Colin GILLE / congelli501
Copyright © 2017 slacka et. al.
Python port - 2019 WaxyMocha

This file is part of WoeUSB-ng.

WoeUSB-ng is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

WoeUSB-ng is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with WoeUSB-ng  If not, see <http://www.gnu.org/licenses/>.
+"""

import subprocess
import sys
import os

if os.getuid() != 0:
    subprocess.run(["pkexec", os.path.realpath(__file__)])
else:
    try:
        import WoeUSB.gui
        WoeUSB.gui.run()
    except SystemExit:
        import WoeUSB.utils

        WoeUSB.utils.update_policy_to_allow_for_running_gui_as_root(__file__)
        print("Policy was updated, please run this program again")

