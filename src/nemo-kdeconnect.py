#!/usr/bin/python3

# Name: KDE Connect Nemo Extension
# Description: KDE Connect Integration for the Nemo file manager
# by JoeJoeTV
# https://github.com/JoeJoeTV/nemo-extension-kdeconnect

EXTENSION_VERSION="1.0.2"

import os, gi, gettext, locale

gi.require_version('Notify', '0.7')
from gi.repository import GObject, Nemo, Gio, GLib, Notify

# Setup localization
try:
    t = gettext.translation(
            "nemo-kdeconnect",
            os.path.dirname(os.path.realpath(__file__)) + "/nemo-kdeconnect/locale",    # nemo-kdeconnect/locale/ subfolder next to script
            fallback=False)
except OSError as e:
    t = gettext.translation(
            "nemo-kdeconnect",
            "/usr/share/locale",    # system locale directory
            fallback=True)

# Install _() function into namespace
t.install()


def get_device_icon(device_type):
    """ Given a device type, returns the fitting icon for the device or a fallback icon """
    if device_type == "desktop":
        return "computer-symbolic"
    elif device_type == "laptop":
        return "laptop-symbolic"
    elif device_type == "smartphone":
        return "smartphone-symbolic"
    elif device_type == "tablet":
        return "tablet-symbolic"
    elif device_type == "tv":
        return "tv-symbolic"
    else:
        return "dialog-question-symbolic"


class KDEConnectMenu(GObject.GObject, Nemo.MenuProvider, Nemo.NameAndDescProvider):
    def __init__(self):
        GObject.GObject.__init__(self)
        
        # Initialize DBus Proxy
        self.dbus_daemon = Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SESSION, Gio.DBusProxyFlags.NONE, None, "org.kde.kdeconnect", "/modules/kdeconnect", "org.kde.kdeconnect.daemon", None)
        
        print(f"[KDEConnectMenu] KDE Connect Nemo Extension v{EXTENSION_VERSION} initialized.")
    
    def send_files(self, menu, files, device):
        """ Tells KDE Connect to send the specified files to the specified device and notifies the user """
        
        # Get list of file URIs
        uri_list = [file.get_uri() for file in files]
        
        # Create DBus proxy for specific device path
        dbus_share = Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SESSION, Gio.DBusProxyFlags.NONE, None, "org.kde.kdeconnect", "/modules/kdeconnect/devices/"+device["id"]+"/share", "org.kde.kdeconnect.device.share", None)
        
        # Convert URI list to GVariant and call DBus function
        variant_uris = GLib.Variant("(as)", (uri_list,))
        dbus_share.call_sync("shareUrls", variant_uris, Gio.DBusCallFlags.NONE, -1, None)
        
        print(f"[KDEConnectMenu] Sending {len(files)} files to {device['name']}({device['id']})")
        
        # Send notification informing the user that the files are being sent
        Notify.init("KDEConnectMenu")
        send_notification = Notify.Notification.new(_("Sending to {device_name}...").format(device_name=device["name"]),
                                _("Sending {num_files} file(s) to device").format(num_files=len(files)),
                                "kdeconnect")
        send_notification.set_urgency(Notify.Urgency.NORMAL)
        send_notification.show()
    
    def get_connected_devices(self):
        """ Gets a list of connected devices from the KDE Connect daemon using DBus """
        
        devices = []
        
        # Get list of available devices from DBus
        params_variant = GLib.Variant("(bb)", (True, True))
        device_ids = self.dbus_daemon.call_sync("devices", params_variant, Gio.DBusCallFlags.NONE, -1, None).unpack()[0]
        device_names = self.dbus_daemon.call_sync("deviceNames", params_variant, Gio.DBusCallFlags.NONE, -1, None).unpack()[0]
        
        for device_id in device_ids:
            dbus_device = Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SESSION, Gio.DBusProxyFlags.NONE, None, "org.kde.kdeconnect", "/modules/kdeconnect/devices/" + str(device_id), "org.kde.kdeconnect.device", None)
            
            device_type = dbus_device.get_cached_property("type").unpack()
            
            # Only add devices to list, which support the Share Plugin
            if "kdeconnect_share" in dbus_device.get_cached_property("supportedPlugins").unpack():
                devices.append({
                    "id": device_id,
                    "name": device_names[device_id],
                    "type": device_type
                })
        
        return devices
        
    def get_file_items(self, window, files):
        # Get list of connected devices
        devices = self.get_connected_devices()
        
        # If there are zero available devices, return greyed-out menu item
        if len(devices) == 0:
            return [
                Nemo.MenuItem(
                    name="KDEConnectMenu::SendViaKDEConnect",
                    label=_("Send via KDE Connect"),
                    tip=_("No devices available to send files to"),
                    icon="kdeconnect",
                    sensitive=False)
            ]
        
        # Only continue if all files are actually files 
        for file in files:
            if (file.get_uri_scheme() != 'file') or file.is_directory():
                return
        
        # Main Menu Item
        main_menuitem = Nemo.MenuItem(name="KDEConnectMenu::SendViaKDEConnect",
                                    label=_("Send via KDE Connect"),
                                    tip=_("Send selected files to connected devices using KDE Connect"),
                                    icon="kdeconnect")
        
        sub_device_menu = Nemo.Menu()
        main_menuitem.set_submenu(sub_device_menu)
        
        # Add Menu Items for each device
        for device in devices:
            device_item = Nemo.MenuItem(name="KDEConnectMenu::SendTo"+device["id"],
                                        label=device["name"],
                                        tip=_("Send File to {device_name}").format(device_name=device["name"]),
                                        icon=get_device_icon(device["type"]))
            
            device_item.connect('activate', self.send_files, files, device)
            sub_device_menu.append_item(device_item)
        
        return [main_menuitem]
    
    def get_name_and_desc(self):
        return [("Nemo KDE Connect:::"+_("Share files to connected devices via KDE Connect directly from within Nemo."))]