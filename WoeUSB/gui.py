#!/usr/bin/env python3

import os
import threading
import time
import wx
import wx.adv
from WoeUSB.core import init, main, cleanup
from WoeUSB.list_devices import usb_drive, dvd_drive

data_directory = os.path.join(os.path.dirname(__file__), "data")

app = wx.App()

_ = wx.GetTranslation

class MainFrame(wx.Frame):
    def __init__(self, title, pos, size, style=wx.DEFAULT_FRAME_STYLE):
        super().__init__(None, title=title, pos=pos, size=size, style=style)
        self.SetIcon(wx.Icon(os.path.join(data_directory, "icon.ico")))

        self.__MainPanel = MainPanel(self)

        self.SetMenuBar(self.create_menu_bar())

    def create_menu_bar(self):
        file_menu = wx.Menu()
        self.__menuItemShowAll = file_menu.AppendCheckItem(wx.ID_ANY, _("Show all drives") + " \tCtrl+A",
                                                           _("Show all drives, even those not detected as USB stick."))
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT)

        help_menu = wx.Menu()
        help_item = help_menu.Append(wx.ID_ABOUT)

        options_menu = wx.Menu()
        self.options_boot = options_menu.AppendCheckItem(wx.ID_ANY, _("Set boot flag"),
                                                         _("Sets boot flag after process of copying."))
        self.options_filesystem = options_menu.AppendCheckItem(wx.ID_ANY, _("Use NTFS"),
                                                               _("Use NTFS instead of FAT. NOTE: NTFS seems to be slower than FAT."))
        self.options_skip_grub = options_menu.AppendCheckItem(wx.ID_ANY, _("Skip legacy grub bootloader"),
                                                               _("No legacy grub bootloader will be created. NOTE: It will only boot on system with UEFI support."))

        menu_bar = wx.MenuBar()
        menu_bar.Append(file_menu, _("&File"))
        menu_bar.Append(options_menu, _("&Options"))
        menu_bar.Append(help_menu, _("&Help"))

        self.Bind(wx.EVT_MENU, self.on_quit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_about, help_item)

        return menu_bar

    def on_quit(self, event):
        self.Close(True)

    def on_about(self, event):
        DialogAbout(self).ShowModal()

    def is_show_all_checked(self):
        return self.__menuItemShowAll.IsChecked()

class MainPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        self.__parent = parent

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Iso / CD
        main_sizer.Add(wx.StaticText(self, label=_("Source :")), 0, wx.ALL, 3)

        # Iso
        self.__isoChoice = wx.RadioButton(self, label=_("From a disk image (iso)"))
        main_sizer.Add(self.__isoChoice, 0, wx.ALL, 3)

        tmp_sizer = wx.BoxSizer(wx.HORIZONTAL)
        tmp_sizer.AddSpacer(20)
        self.__isoFile = wx.FilePickerCtrl(self, wx.ID_ANY, "", _("Please select a disk image"),
                                           "Iso images (*.iso)|*.iso;*.ISO|All files|*")
        tmp_sizer.Add(self.__isoFile, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM, 3)
        main_sizer.Add(tmp_sizer, 0, wx.EXPAND, 0)

        # DVD
        self.__dvdChoice = wx.RadioButton(self, label=_("From a CD/DVD drive"))
        main_sizer.Add(self.__dvdChoice, 0, wx.ALL, 3)

        # List
        tmp_sizer = wx.BoxSizer(wx.HORIZONTAL)
        tmp_sizer.AddSpacer(20)
        self.__dvdDriveList = wx.ListBox(self, wx.ID_ANY)
        tmp_sizer.Add(self.__dvdDriveList, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 3)
        main_sizer.Add(tmp_sizer, 1, wx.EXPAND, 0)

        # Target
        main_sizer.AddSpacer(20)

        main_sizer.Add(wx.StaticText(self, wx.ID_ANY, _("Target device :")), 0, wx.ALL, 3)

        # List
        self.__usbStickList = wx.ListBox(self, wx.ID_ANY)
        main_sizer.Add(self.__usbStickList, 1, wx.EXPAND | wx.ALL, 3)

        # Buttons
        main_sizer.AddSpacer(30)

        bt_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__btRefresh = wx.Button(self, wx.ID_REFRESH)
        bt_sizer.Add(self.__btRefresh, 0, wx.ALL, 3)
        self.__btInstall = wx.Button(self, wx.ID_ANY, _("Install"))
        bt_sizer.Add(self.__btInstall, 0, wx.ALL, 3)

        main_sizer.Add(bt_sizer, 0, wx.ALIGN_RIGHT, 0)

        self.SetSizer(main_sizer)

        self.Bind(wx.EVT_BUTTON, self.on_install, self.__btInstall)
        self.Bind(wx.EVT_BUTTON, self.on_refresh, self.__btRefresh)
        self.Bind(wx.EVT_RADIOBUTTON, self.on_source_option_changed, self.__isoChoice)
        self.Bind(wx.EVT_RADIOBUTTON, self.on_source_option_changed, self.__dvdChoice)

        self.refresh_list_content()
        self.on_source_option_changed(wx.CommandEvent)
        self.__btInstall.Enable(self.is_install_ok())

    def refresh_list_content(self):
        self.__usbStickList.Clear()

        show_all_checked = self.__parent.is_show_all_checked()

        device_list = usb_drive(show_all_checked)

        for device in device_list:
            self.__usbStickList.Append(device[1])

        self.__dvdDriveList.Clear()

        drive_list = dvd_drive()

        for drive in drive_list:
            self.__dvdDriveList.Append(drive[1])

        self.__btInstall.Enable(self.is_install_ok())

    def on_source_option_changed(self, event):
        is_iso = self.__isoChoice.GetValue()

        self.__isoFile.Enable(is_iso)
        self.__dvdDriveList.Enable(not is_iso)

        self.__btInstall.Enable(self.is_install_ok())

    def is_install_ok(self):
        is_iso = self.__isoChoice.GetValue()
        return ((is_iso and os.path.isfile(self.__isoFile.GetPath())) or (
                not is_iso and self.__dvdDriveList.GetSelection() != wx.NOT_FOUND)) and self.__usbStickList.GetSelection() != wx.NOT_FOUND

    def on_install(self, event):
        if wx.MessageBox(
            _("Are you sure? This will delete all your files and wipe out the selected partition."),
            _("Cancel"),
            wx.YES_NO | wx.ICON_QUESTION | wx.NO_DEFAULT,
            self) != wx.YES:
            return

        if self.is_install_ok():
            is_iso = self.__isoChoice.GetValue()

            device = usb_drive()[self.__usbStickList.GetSelection()][0]

            if is_iso:
                iso = self.__isoFile.GetPath()
            else:
                iso = dvd_drive()[self.__dvdDriveList.GetSelection()][0]

            filesystem = "NTFS" if self.__parent.options_filesystem.IsChecked() else "FAT"

            boot_flag = self.__parent.options_boot.IsChecked()
            skip_grub = self.__parent.options_skip_grub.IsChecked()

            woe = WoeUSB_handler(iso, device, boot_flag, filesystem, skip_grub)
            woe.start()

            dialog = wx.ProgressDialog(_("Installing"), _("Please wait..."), 101, self.GetParent(),
                                       wx.PD_APP_MODAL | wx.PD_SMOOTH | wx.PD_CAN_ABORT)

            while woe.is_alive():
                if not woe.progress:
                    status = dialog.Pulse(woe.state)[0]
                    time.sleep(0.06)
                else:
                    status = dialog.Update(woe.progress, woe.state)[0]

                if not status:
                    if wx.MessageBox(_("Are you sure you want to cancel the installation?"), _("Cancel"),
                                     wx.YES_NO | wx.ICON_QUESTION, self) == wx.NO:
                        dialog.Resume()
                    else:
                        woe.kill = True
                        break
            dialog.Destroy()

            if woe.error == "":
                wx.MessageBox(_("Installation succeeded!"), _("Installation"), wx.OK | wx.ICON_INFORMATION, self)
            else:
                wx.MessageBox(_("Installation failed!") + "\n" + str(woe.error), _("Installation"),
                              wx.OK | wx.ICON_ERROR, self)

    def on_refresh(self, event):
        self.refresh_list_content()

class DialogAbout(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title=_("About"), size=(650, 590))

        self.create_widgets()

    def create_widgets(self):
        sizer_all = wx.BoxSizer(wx.VERTICAL)
        sizer_img = wx.BoxSizer(wx.HORIZONTAL)

        img = wx.Image(os.path.join(data_directory, "icon.ico"), wx.BITMAP_TYPE_ICO).Scale(48, 48, wx.IMAGE_QUALITY_BILINEAR)
        bitmapIcone = wx.StaticBitmap(self, wx.ID_ANY, wx.Bitmap(img), wx.DefaultPosition, wx.Size(48, 48))
        sizer_img.Add(bitmapIcone, 0, wx.ALL, 5)

        sizer_text = wx.BoxSizer(wx.VERTICAL)

        staticTextTitre = wx.StaticText(self, wx.ID_ANY, "WoeUSB-ng")
        staticTextTitre.SetFont(wx.Font(16, 74, 90, 92, False, "Sans"))
        staticTextTitre.SetForegroundColour(wx.Colour(0, 60, 118))
        sizer_text.Add(staticTextTitre, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 5)

        staticTextVersion = wx.StaticText(self, wx.ID_ANY, _("VERSION"))
        staticTextVersion.SetFont(wx.Font(10, 74, 90, 92, False, "Sans"))
        staticTextVersion.SetForegroundColour(wx.Colour(69, 141, 196))
        sizer_text.Add(staticTextVersion, 0, wx.LEFT, 5)
        sizer_img.Add(sizer_text, 0, 0, 5)
        sizer_all.Add(sizer_img, 0, wx.EXPAND, 5)

        notebookAutorLicence = wx.Notebook(self, wx.ID_ANY)

        notebookAutorLicence.AddPage(
            PanelNoteBookAutors(notebookAutorLicence, _("Authors"), "slacka \nLin-Buo-Ren\nWaxyMocha", os.path.join(data_directory, "woeusb-logo.png"),
                                "github.com/WoeUSB/WoeUSB-ng"), _("Authors"), True)
        notebookAutorLicence.AddPage(
            PanelNoteBookAutors(notebookAutorLicence, _("Original WinUSB Developer"), "Colin GILLE / Congelli501",
                                os.path.join(data_directory, "c501-logo.png"), "www.congelli.eu"), _("Original WinUSB Developer"), False)

        licence_str = _(
            '''
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
            along with WoeUSB-ng.  If not, see <http://www.gnu.org/licenses/>.
            ''')

        licence_txt = wx.TextCtrl(notebookAutorLicence, wx.ID_ANY, licence_str, wx.DefaultPosition,
                                  wx.DefaultSize, wx.TE_MULTILINE | wx.TE_READONLY)

        notebookAutorLicence.AddPage(licence_txt, _("License"))

        sizer_all.Add(notebookAutorLicence, 1, wx.EXPAND | wx.ALL, 5)

        btOk = wx.Button(self, wx.ID_OK)
        sizer_all.Add(btOk, 0, wx.ALIGN_RIGHT | wx.BOTTOM | wx.RIGHT, 5)
        btOk.SetFocus()

        self.SetSizer(sizer_all)
        self.Layout()

class PanelNoteBookAutors(wx.Panel):
    def __init__(self, parent, title, autherName, imgName, siteLink):
        super().__init__(parent)

        sizer_note_book_autors = wx.BoxSizer(wx.VERTICAL)

        auteur_static_text = wx.StaticText(self, wx.ID_ANY, autherName)
        sizer_note_book_autors.Add(auteur_static_text, 0, wx.ALL, 5)

        if siteLink != "":
            autor_link = wx.adv.HyperlinkCtrl(self, wx.ID_ANY, siteLink, siteLink)
            sizer_note_book_autors.Add(autor_link, 0, wx.LEFT | wx.BOTTOM, 5)

        if imgName != "":
            img = wx.Image(imgName, wx.BITMAP_TYPE_PNG)
            img_autor_logo = wx.StaticBitmap(self, wx.ID_ANY, wx.Bitmap(img))
            sizer_note_book_autors.Add(img_autor_logo, 0, wx.LEFT, 5)

        self.SetSizer(sizer_note_book_autors)

class WoeUSB_handler(threading.Thread):
    def __init__(self, source, target, boot_flag, filesystem, skip_grub=False):
        super().__init__()

        self.progress = False
        self.state = ""
        self.error = ""
        self.kill = False

        init(from_cli=False, install_mode="device", source_media=source, target_media=target)
        self.source = source
        self.target = target
        self.boot_flag = boot_flag
        self.filesystem = filesystem
        self.skip_grub = skip_grub

    def run(self):
        source_fs_mountpoint, target_fs_mountpoint, temp_directory, target_media = init(from_cli=False, install_mode="device", source_media=self.source, target_media=self.target)
        try:
            main(source_fs_mountpoint, target_fs_mountpoint, self.source, self.target, "device", temp_directory, self.filesystem, self.boot_flag, None, self.skip_grub)
        except SystemExit:
            pass

        cleanup(source_fs_mountpoint, target_fs_mountpoint, temp_directory, target_media)

def run():
    frameTitle = "WoeUSB-ng"

    frame = MainFrame(frameTitle, wx.DefaultPosition, wx.Size(400, 600))
    frame.SetMinSize(wx.Size(300, 450))

    frame.Show(True)
    app.MainLoop()

if __name__ == "__main__":
    run()
