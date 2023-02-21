from setuptools import setup

setup(
    data_files=[
        ("share/applications", ["miscellaneous/WoeUSB-ng.desktop"]),
        ("share/polkit-1/actions", ["miscellaneous/com.github.woeusb.woeusb-ng.policy"]),
        ("share/icons/hicolor/scalable/apps", ["src/WoeUSB/data/woeusb-logo.png"]),
    ],
    install_requires=[
        'termcolor',
        'wxPython',
    ]
)
