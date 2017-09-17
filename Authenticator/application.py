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

from gi import require_version
require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gio, Gdk, GObject
from .widgets import SettingsWindow, Window, AboutDialog, ShortcutsWindow
from .models import Settings, Keyring, Clipboard, Logger
from .utils import is_gnome


class Application(Gtk.Application):
    """Authenticator application object."""

    def __init__(self):
        Gtk.Application.__init__(self,
                                 application_id="org.gnome.Authenticator",
                                 flags=Gio.ApplicationFlags.FLAGS_NONE)
        GLib.set_application_name(_("Gnome Authenticator"))
        GLib.set_prgname("Gnome Authenticator")
        self.alive = True
        self.menu = Gio.Menu()

    def setup_css(self):
        """Setup the CSS and load it."""
        if Gtk.get_major_version() >= 3 and Gtk.get_minor_version() >= 20:
            filename = "org.gnome.Authenticator-post3.20.css"
        else:
            filename = "org.gnome.Authenticator-pre3.20.css"
        uri = 'resource:///org/gnome/Authenticator/{}'.format(filename)
        provider_file = Gio.File.new_for_uri(uri)
        provider = Gtk.CssProvider()
        screen = Gdk.Screen.get_default()
        context = Gtk.StyleContext()
        provider.load_from_file(provider_file)
        context.add_provider_for_screen(screen, provider,
                                        Gtk.STYLE_PROVIDER_PRIORITY_USER)
        Logger.debug("Loading CSS")

    def do_startup(self):
        """Startup the application."""
        Gtk.Application.do_startup(self)
        # Unlock the keyring
        if not Keyring.unlock():
            self.on_quit()
        self.generate_menu()
        self.setup_css()

        # Set the default night mode
        is_night_mode = Settings.get_default().is_night_mode
        gtk_settings = Gtk.Settings.get_default()
        gtk_settings.set_property("gtk-application-prefer-dark-theme",
                                  is_night_mode)

    def generate_menu(self):
        """Generate application menu."""
        settings = Settings.get_default()
        # Settings section
        settings_content = Gio.Menu.new()
        settings_content.append_item(Gio.MenuItem.new(_("Settings"),
                                                      "app.settings"))
        settings_section = Gio.MenuItem.new_section(None, settings_content)
        self.menu.append_item(settings_section)

        # Help section
        help_content = Gio.Menu.new()
        # Night mode action
        help_content.append_item(Gio.MenuItem.new(_("Night Mode"),
                                                  "app.night_mode"))
        # Shortcuts action
        if Gtk.get_major_version() >= 3 and Gtk.get_minor_version() >= 20:
            help_content.append_item(Gio.MenuItem.new(_("Shortcuts"),
                                                      "app.shortcuts"))

        help_content.append_item(Gio.MenuItem.new(_("About"), "app.about"))
        help_content.append_item(Gio.MenuItem.new(_("Quit"), "app.quit"))
        help_section = Gio.MenuItem.new_section(None, help_content)
        self.menu.append_item(help_section)

        action = Gio.SimpleAction.new("settings", None)
        action.connect("activate", self.on_settings)
        action.set_enabled(not settings.is_locked)
        settings.bind('locked', action, 'enabled',
                      Gio.SettingsBindFlags.INVERT_BOOLEAN)
        self.add_action(action)

        is_night_mode = settings.is_night_mode
        gv_is_night_mode = GLib.Variant.new_boolean(is_night_mode)
        action = Gio.SimpleAction.new_stateful("night_mode", None,
                                               gv_is_night_mode)
        action.connect("change-state", self.on_night_mode)
        self.add_action(action)

        if Gtk.get_major_version() >= 3 and Gtk.get_minor_version() >= 20:
            action = Gio.SimpleAction.new("shortcuts", None)
            action.connect("activate", self.on_shortcuts)
            self.add_action(action)

        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.on_about)
        self.add_action(action)

        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self.on_quit)
        self.add_action(action)
        if is_gnome():
            self.set_app_menu(self.menu)
            Logger.debug("Adding Application Menu")

    def do_activate(self, *args):
        """On activate signal override."""
        window = Window.get_default()
        window.set_application(self)
        window.connect("delete-event", lambda x, y: self.on_quit())
        self.add_window(window)
        window.show_all()
        window.present()

    def on_night_mode(self, action, *args):
        """Switch night mode."""
        settings = Settings.get_default()
        is_night_mode = not settings.is_night_mode
        action.set_state(GLib.Variant.new_boolean(is_night_mode))
        settings.is_night_mode = is_night_mode
        gtk_settings = Gtk.Settings.get_default()
        gtk_settings.set_property("gtk-application-prefer-dark-theme",
                                  is_night_mode)

    def on_shortcuts(self, *args):
        """Shows keyboard shortcuts."""
        if Gtk.get_major_version() >= 3 and Gtk.get_minor_version() >= 20:
            shortcuts = ShortcutsWindow()
            shortcuts.set_transient_for(Window.get_default())
            shortcuts.show()

    def on_about(self, *args):
        """
            Shows about dialog
        """
        dialog = AboutDialog()
        dialog.set_transient_for(Window.get_default())
        dialog.run()
        dialog.destroy()

    def on_settings(self, *args):
        """
            Shows settings window
        """
        settings_window = SettingsWindow()
        settings_window.set_attached_to(Window.get_default())
        settings_window.show_window()

    def on_quit(self, *args):
        """
        Close the application, stops all threads
        and clear clipboard for safety reasons
        """
        Clipboard.clear()
        from .widgets.accounts.list import AccountsList
        accounts = AccountsList.get_default()
        for account_row in accounts:
            account_row.account.kill()

        window = Window.get_default()
        window.save_state()
        window.destroy()
        self.quit()
