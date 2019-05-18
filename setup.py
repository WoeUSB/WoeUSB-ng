from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install
from xml.dom.minidom import parse
import shutil
import os


class PostDevelopCommand(develop):
    """Post-installation for development mode."""

    def run(self):
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION
        develop.run(self)


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        working_directory = os.path.abspath(os.path.dirname(__file__))
        path = self.install_scripts + "/woeusbgui"

        dom = parse(working_directory + '/polkit/com.github.woeusb.woeusb-ng.policy')
        for action in dom.getElementsByTagName('action'):
            if action.getAttribute('id') == "com.github.slacka.woeusb.run-gui-using-pkexec":
                for annotate in action.getElementsByTagName('annotate'):
                    if annotate.getAttribute('key') == "org.freedesktop.policykit.exec.path":
                        annotate.childNodes[0].nodeValue = path

        with open(working_directory + '/polkit/com.github.woeusb.woeusb-ng.policy', "w") as file:
            dom.writexml(file)

        shutil.copy2(working_directory + '/polkit/com.github.woeusb.woeusb-ng.policy', "/usr/share/polkit-1/actions")
        install.run(self)


setup(
    name='WoeUSB-ng',
    version_config={
        "version_format": "{tag}.dev{sha}",
        "starting_version": "0.1.2"
    },
    description='Create bootable windows installer',
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
    setup_requires=[
        'better-setuptools-git-version'
    ],
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand
    }
)
