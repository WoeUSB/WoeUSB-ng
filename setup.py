from setuptools import setup

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
