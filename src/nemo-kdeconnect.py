#!/usr/bin/python3

# Name: KDE Connect Nemo Extension
# Description: KDE Connect Integration for the Nemo file manager
# by JoeJoeTV
# https://github.com/JoeJoeTV/KDEConnectNemoExtension
# Version: 1.0

import gi

gi.require_version('Notify', '0.7')
from gi.repository import GObject, Nemo, Gtk, Gio, GLib, Notify

import gettext, locale

locale_dir = "./nemo-kdeconnect/locale" # GLib.get_home_dir() + "/.local/share/locale"
locale_domain = "nemo-kdeconnect"

# Get correct icon name from device type string
def get_device_icon(device_type):
    if device_type == "dektop":
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
    
    def send_files(self, menu, files, device):
        # Setup translation
        locale.setlocale(locale.LC_ALL, "")
        gettext.bindtextdomain(locale_domain, locale_dir)
        gettext.textdomain(locale_domain)
        _ = gettext.gettext
        
        # Add all file URIs to a list
        uri_list = []
        for file in files:
            uri_list.append(file.get_uri())
        
        try:
            dbus_share = Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SESSION, Gio.DBusProxyFlags.NONE, None, "org.kde.kdeconnect", "/modules/kdeconnect/devices/"+device["id"]+"/share", "org.kde.kdeconnect.device.share", None)
            
            # Convert URI list to GVariant and call DBus function
            variant_uris = GLib.Variant("(as)", (uri_list,))
            dbus_share.call_sync("shareUrls", variant_uris, Gio.DBusCallFlags.NONE, -1, None)
        except Exception as e:
            raise Exception(e)
        
        print("[KDEConnectMenu] Sending "+str(len(files))+" files to "+device["name"]+"("+device["id"]+")")
        
        # Send notification informing the user that the files are being sent
        Notify.init("KDEConnectMenu")
        send_notification = Notify.Notification.new(_("Sending to {device_name}...").format(device_name=device["name"]),
                                _("Sending {num_files} file(s) to device").format(num_files=len(files)),
                                "kdeconnect")
        send_notification.set_urgency(Notify.Urgency.NORMAL)
        send_notification.show()
    
    def get_connected_devices(self):
        devices = []
        
        try:
            # Get list of available devices from DBus
            params_variant = GLib.Variant("(bb)", (True, True))        
            device_ids = self.dbus_daemon.call_sync("devices", params_variant, Gio.DBusCallFlags.NONE, -1, None).unpack()[0]
            device_names = self.dbus_daemon.call_sync("deviceNames", params_variant, Gio.DBusCallFlags.NONE, -1, None).unpack()[0]
            
            for device_id in device_ids:
                dbus_device = Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SESSION, Gio.DBusProxyFlags.NONE, None, "org.kde.kdeconnect", "/modules/kdeconnect/devices/" + str(device_id), "org.kde.kdeconnect.device", None)
                
                device_type = dbus_device.get_cached_property("type").unpack()
                
                # Only add devices to list, which support the Share Plugin
                if "kdeconnect_share" in dbus_device.get_cached_property("supportedPlugins").unpack():                
                    element = {
                        "id": device_id,
                        "name": device_names[device_id],
                        "type": device_type
                    }
                    devices.append(element)
                
        except Exception as e:
            raise Exception(e)
        
        return devices
        
    def get_file_items(self, window, files):
        # Get list of connected devices
        devices = self.get_connected_devices()
        
        # If there are zero available devices, do nothing
        if len(devices) == 0:
            return
        
        # Only continue if all files are actually files 
        for file in files:
            if file.get_uri_scheme() != 'file' or file.is_directory():
                #print("NO FILE GODDAMNIT!!!")
                return
        
        # Setup translation
        locale.setlocale(locale.LC_ALL, "")
        gettext.bindtextdomain(locale_domain, locale_dir)
        gettext.textdomain(locale_domain)
        _ = gettext.gettext
        
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
        # Setup translation
        locale.setlocale(locale.LC_ALL, "")
        gettext.bindtextdomain(locale_domain, locale_dir)
        gettext.textdomain(locale_domain)
        _ = gettext.gettext
        return [("Nemo KDE Connect:::"+_("Share files to connected devices via KDE Connect directly from within Nemo."))]