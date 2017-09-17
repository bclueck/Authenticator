"""
 Copyright © 2017 Bilal Elmoussaoui <bil.elmoussaoui@gmail.com>

 This file is part of Gnome Authenticator.

 Gnome Authenticator is free software: you can redistribute it and/or
 modify it under the terms of the GNU General Public License as published
 by the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 TwoFactorAuth is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Gnome Authenticator. If not, see <http://www.gnu.org/licenses/>.
"""
from gettext import gettext as _
import json

from gi import require_version
require_version("Gtk", "3.0")
from gi.repository import Gio, Gtk

from ..headerbar import HeaderBarButton, HeaderBarToggleButton
from ..inapp_notification import InAppNotification


class AddAcountWindow(Gtk.Window):
    """Add Account Window."""
    STEP = 1

    def __init__(self):
        Gtk.Window.__init__(self)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self.set_resizable(False)
        self.set_size_request(400, 600)
        self.resize(400, 600)
        self._signals = {}
        self._build_widgets()

    def _build_widgets(self):
        """Create the Add Account widgets."""
        # Header Bar
        headerbar = Gtk.HeaderBar()
        headerbar.set_show_close_button(False)
        headerbar.set_title(_("Add a new account"))
        self.set_titlebar(headerbar)
        # Next btn
        self.next_btn = Gtk.Button()
        self.next_btn.get_style_context().add_class("suggested-action")
        headerbar.pack_end(self.next_btn)

        # Search btn
        self.search_btn = HeaderBarToggleButton("system-search-symbolic",
                                                _("Search"))
        headerbar.pack_end(self.search_btn)
        # QR code scan btn
        self.scan_btn = HeaderBarButton("qrscanner-symbolic",
                                        _("Scan QR code"))
        headerbar.pack_end(self.scan_btn)

        # Back btn
        self.back_btn = Gtk.Button()

        headerbar.pack_start(self.back_btn)

        # Main stack
        self.main = Gtk.Stack()
        self.accounts_list = AccountsList()
        # Create a scrolled window for the accounts list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER,
                            Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.accounts_list)
        self.main.add_named(scrolled, "1")
        self.account_conifg = AccountConfig()
        self.main.add_named(self.account_conifg, "2")

        self.add(self.main)
        # The first step!
        self._set_step(1)

    def _set_step(self, step):
        AddAcountWindow.STEP = step
        search_btn_visible = False
        scan_btn_visible = False
        if self._signals:
            self.back_btn.disconnect(self._signals["back"])
            self.next_btn.disconnect(self._signals["next"])
        if step == 1:
            next_lbl = _("Next")
            back_lbl = _("Close")
            search_btn_visible = True
            self._signals["back"] = self.back_btn.connect("clicked",
                                                          self._on_quit)
            self._signals["next"] = self.next_btn.connect("clicked",
                                                          lambda x: self._set_step(2))
        elif step == 2:
            next_lbl = _("Add")
            back_lbl = _("Back")
            scan_btn_visible = True
            account = self.accounts_list.get_selected_row()
            self.account_conifg.set_account(account)
            self._signals["back"] = self.back_btn.connect("clicked",
                                                          lambda x: self._set_step(1))
            self._signals["next"] = self.next_btn.connect("clicked",
                                                          self._on_add)
        self.next_btn.set_label(next_lbl)
        self.back_btn.set_label(back_lbl)

        self.scan_btn.set_visible(scan_btn_visible)
        self.scan_btn.set_no_show_all(not scan_btn_visible)

        self.search_btn.set_visible(search_btn_visible)
        self.search_btn.set_no_show_all(not search_btn_visible)

        self.main.set_visible_child_name(str(step))

    def _on_quit(self, *args):
        self.destroy()

    def _on_add(self, *args):
        print(args)

class AccountsList(Gtk.ListBox):

    def __init__(self):
        Gtk.ListBox.__init__(self)
        self.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._fill_data()

    def _fill_data(self):
        uri = 'resource:///org/gnome/Authenticator/data.json'
        file = Gio.File.new_for_uri(uri)
        content = str(file.load_contents(None)[1].decode("utf-8"))
        data = json.loads(content)
        for name, logo in data.items():
            self.add(AccountRow(name, logo))


class AccountRow(Gtk.ListBoxRow):

    def __init__(self, name, logo):
        Gtk.ListBoxRow.__init__(self)
        self.name = name
        self.logo = logo
        self._build_widgets()

    def _build_widgets(self):
        container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        theme = Gtk.IconTheme.get_default()
        if theme.has_icon(self.logo):
            icon_name = self.logo
        else:
            icon_name = "image-missing"
        logo_img = Gtk.Image.new_from_icon_name(icon_name,
                                                Gtk.IconSize.DIALOG)
        container.pack_start(logo_img, False, False, 6)

        name_lbl = Gtk.Label(self.name)
        name_lbl.get_style_context().add_class("account-name")
        name_lbl.set_halign(Gtk.Align.START)
        container.pack_start(name_lbl, False, False, 6)
        self.add(container)


class AccountConfig(Gtk.Box):

    def __init__(self):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self.notification = InAppNotification()
        self.logo_img = Gtk.Image()
        self.name_entry = Gtk.Entry()
        self.secret_entry = Gtk.Entry()
        self._build_widgets()

    def _build_widgets(self):
        self.pack_start(self.notification, False, False, 0)

        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container.set_border_width(18)

        self.name_entry.set_placeholder_text(_("Account name"))
        self.secret_entry.set_placeholder_text(_("Secret Token"))

        container.pack_start(self.logo_img, False, False, 6)
        container.pack_end(self.secret_entry, False, False, 6)
        container.pack_end(self.name_entry, False, False, 6)

        self.pack_start(container, False, False, 6)


    def set_account(self, account):
        name = account.name
        logo = account.logo

        self.name_entry.set_text(name)
        theme = Gtk.IconTheme.get_default()
        if theme.has_icon(logo):
            self.logo_img.set_from_icon_name(logo,
                                             Gtk.IconSize.DIALOG)
        else:
            self.logo_img.set_from_icon_name("image-missing",
                                             Gtk.IconSize.DIALOG)
