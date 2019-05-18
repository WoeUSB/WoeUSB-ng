from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install
from xml.dom.minidom import parse
import shutil
import os

this_directory = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


class PostDevelopCommand(develop):
    """Post-installation for development mode."""

    def run(self):
        # TODO
        develop.run(self)


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        path = self.install_scripts + "/woeusbgui"

        dom = parse(this_directory + '/polkit/com.github.woeusb.woeusb-ng.policy')
        for action in dom.getElementsByTagName('action'):
            if action.getAttribute('id') == "com.github.slacka.woeusb.run-gui-using-pkexec":
                for annotate in action.getElementsByTagName('annotate'):
                    if annotate.getAttribute('key') == "org.freedesktop.policykit.exec.path":
                        annotate.childNodes[0].nodeValue = path

        with open(this_directory + '/polkit/com.github.woeusb.woeusb-ng.policy', "w") as file:
            dom.writexml(file)

        shutil.copy2(this_directory + '/polkit/com.github.woeusb.woeusb-ng.policy', "/usr/share/polkit-1/actions")
        install.run(self)


setup(
    name='WoeUSB-ng',
    version='0.1.5',
    description='A Linux program to create a Windows USB stick installer from a real Windows DVD or image.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='http://github.com/WoeUSB/WoeUSB-ng',
    author='Jakub Szymański',
    author_email='jakubmateusz@poczta.onet.pl',
    license='GPL-3',
    zip_safe=False,
    packages=['WoeUSB'],
    include_package_data=True,
    scripts=[
        'WoeUSB/woeusb',
        'WoeUSB/woeusbgui'
    ],
    install_requires=[
        'termcolor',
        'wxPython'
    ],
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand
    }
)
