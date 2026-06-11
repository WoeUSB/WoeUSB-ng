#!/usr/bin/env python3


def run():
    try:
        import WoeUSB.gui
    except ImportError as error:
        if error.name == 'wx':
            print('WoeUSB-ng GUI dependencies are not installed.')
            print("Install them with: pip install 'WoeUSB-ng[gui]'")
            raise SystemExit(1)
        raise

    WoeUSB.gui.run()
