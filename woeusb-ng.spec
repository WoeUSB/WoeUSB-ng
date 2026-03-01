Name:           woeusb-ng
Version:        0.2.12
Release:        1%{?dist}
Summary:        Create Windows USB installer from an ISO image or DVD

License:        GPL-3.0-or-later
URL:            https://github.com/WoeUSB/WoeUSB-ng
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  pyproject-rpm-macros

# Core runtime tools
Requires:       util-linux
Requires:       parted
Requires:       dosfstools
Requires:       ntfsprogs
Requires:       grub2-tools
Requires:       p7zip
Requires:       wimlib-utils

# Python dependencies
Requires:       python3-termcolor
Requires:       python3-wxpython4

%description
WoeUSB-ng is a simple tool that enables you to create your own USB stick
Windows installer from an ISO image or a real DVD.

It supports creating bootable USB drives for Windows Vista through Windows 11,
using either FAT32 or NTFS filesystems, with both BIOS and UEFI boot support.

This is a rewrite of the original WoeUSB project.

%prep
%autosetup -n WoeUSB-ng-%{version}

# Fix polkit policy: package installs binaries to %%{_bindir}, not /usr/local/bin
sed -i 's|/usr/local/bin/woeusbgui|%{_bindir}/woeusbgui|' \
    miscellaneous/com.github.woeusb.woeusb-ng.policy

%build
%pyproject_wheel

%install
%pyproject_install

%files
%license COPYING
%doc README.md
%{python3_sitelib}/WoeUSB/
%{python3_sitelib}/woeusb_ng-%{version}.dist-info/
%{_bindir}/woeusb
%{_bindir}/woeusbgui
%{_datadir}/applications/WoeUSB-ng.desktop
%{_datadir}/polkit-1/actions/com.github.woeusb.woeusb-ng.policy
%{_datadir}/icons/hicolor/scalable/apps/woeusb-logo.png

%changelog
* Sun Mar 01 2026 Packager <packager@example.com> - 0.2.12-1
- Initial RPM packaging for Fedora
