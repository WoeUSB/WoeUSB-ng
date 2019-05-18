from setuptools import setup
from xml.dom.minidom import parse
import shutil

setup(name='WoeUSB-ng',
      version='0.1',
      description='Create bootable windows installer',
      url='http://github.com/WoeUSB/WoeUSB-ng',
      author='Jakub Szymański',
      author_email='jakubmateusz@poczta.onet.pl',
      license='GPL-3',
      zip_safe=False,
      packages=['WoeUSB'],
      scripts=[
            'WoeUSB/woeusb',
            'WoeUSB/woeusbgui'
      ],
      install_requires=[
          'termcolor',
          'wxPython'
      ]
      )

path = "/usr/bin/woeusbgui"
dom = parse('./polkit/com.github.woeusb.woeusb-ng.policy')
for action in dom.getElementsByTagName('action'):
    if action.getAttribute('id') == "com.github.slacka.woeusb.run-gui-using-pkexec":
        for annotate in action.getElementsByTagName('annotate'):
            if annotate.getAttribute('key') == "org.freedesktop.policykit.exec.path":
                annotate.childNodes[0].nodeValue = path

polkit = open('./polkit/com.github.woeusb.woeusb-ng.policy', "w")
dom.writexml(polkit)

shutil.copy2('./polkit/com.github.woeusb.woeusb-ng.policy', "/usr/share/polkit-1/actions")
