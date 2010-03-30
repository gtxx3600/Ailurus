#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Ailurus - make Linux easier to use
#
# Copyright (C) 2007-2010, Trusted Digital Technology Laboratory, Shanghai Jiao Tong University, China.
#
# Ailurus is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Ailurus is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ailurus; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

from __future__ import with_statement
import gtk, os, sys
from lib import *
from libu import *
from loader import *

def detect_running_instances():
    string = get_output('ps -a -u $USER | grep ailurus', True)
    if string!='':
        notify(_('Warning!'), 
           _('Another instance of Ailurus is running. '
              'It is not recommended to run multiple instance concurrently.') )

def change_task_name():
    import ctypes
    libc = ctypes.CDLL('libc.so.6')
    libc.prctl(15, 'ailurus', 0, 0, 0)

def set_default_window_icon():
    gtk.window_set_default_icon_from_file(D+'suyun_icons/default.png')

def with_same_content(file1, file2):
    with open(file1) as f:
        content1 = f.read()
    with open(file2) as f:
        content2 = f.read()
    return content1 == content2

def check_dbus_configuration():
    same_content = True
    if not with_same_content('/etc/dbus-1/system.d/cn.ailurus.conf', '/usr/share/ailurus/support/cn.ailurus.conf'):
        same_content = False
    if not with_same_content('/usr/share/dbus-1/system-services/cn.ailurus.service', '/usr/share/ailurus/support/cn.ailurus.service'):
        same_content = False
    dbus_ok = True
    try:
        get_authentication_method()
    except:
        dbus_ok = False
    if same_content and dbus_ok: return
    import StringIO
    message = StringIO.StringIO()
    print >>message, _('Error happened. You cannot install any software by Ailurus. :(')
    print >>message, ''
    if not same_content:
        print >>message, _('System configuration file should be updated.')
        print >>message, _('Please run these commands using <b>su</b> or <b>sudo</b>:')
        print >>message, ''
        print >>message, '<span color="blue">', 'cp /usr/share/ailurus/support/cn.ailurus.conf /etc/dbus-1/system.d/cn.ailurus.conf', '</span>'
        print >>message, '<span color="blue">', 'cp /usr/share/ailurus/support/cn.ailurus.service /usr/share/dbus-1/system-services/cn.ailurus.service', '</span>'
        print >>message, ''
    if not dbus_ok:
        print >>message, _("Ailurus' D-Bus daemon exited with error.")
        print >>message, _("Please restart your computer, or start daemon using <b>su</b> or <b>sudo</b>:")
        print >>message, ''
        print >>message, '<span color="blue">', '/usr/share/ailurus/support/ailurus-daemon &amp;', '</span>'
    dialog = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
    dialog.set_title('Ailurus ' + AILURUS_VERSION)
    dialog.set_markup(message.getvalue())
    dialog.run()
    dialog.destroy()

def get_desktop_environment():
    if Config.is_GNOME():
        import gnome
        return gnome
    else:
        return None

def get_distribution():
    if Config.is_Mint():
        try:
            versions = ['hardy', 'intrepid', 'jaunty', 'karmic', 'lucid', ]
            rs = Config.get_Mint_version()
            if rs in ['5', '6', '7', '8', '9']:
                version = versions[int(rs)-5]
            Config.set_Ubuntu_version( version )
            import ubuntu
            return ubuntu
        except:
            import traceback
            traceback.print_exc()
            return None
    elif Config.is_Ubuntu(): 
        import ubuntu
        return ubuntu
    elif Config.is_Fedora():
        import fedora
        return fedora
    else:
        return None

def wait_firefox_to_create_profile():
    if os.path.exists('/usr/bin/firefox'):
        propath = os.path.expanduser('~/.mozilla/firefox/profiles.ini')
        if not os.path.exists(propath):
            KillWhenExit.add('firefox -no-remote')
            import time
            start = time.time()
            while not os.path.exists(propath) and time.time() - start < 6:
                time.sleep(0.1)

def exception_happened(etype, value, tb):
    if etype == KeyboardInterrupt: return
    
    import traceback, StringIO
    msg = StringIO.StringIO()
    print >>msg, _('Traceback:')
    traceback.print_tb(tb, file=msg)
    print >>msg, etype, ':', value

    title_box = gtk.HBox(False, 5)
    import os
    if os.path.exists(D+'umut_icons/bug.png'):
        image = gtk.Image()
        image.set_from_file(D+'umut_icons/bug.png')
        title_box.pack_start(image, False)
    title = label_left_align( _('A bug appears. Would you please tell Ailurus developers? Thank you!') )
    title_box.pack_start(title, False)
    
    textview_traceback = gtk.TextView()
    gray_bg(textview_traceback)
    textview_traceback.set_wrap_mode(gtk.WRAP_WORD)
    textview_traceback.get_buffer().set_text(msg.getvalue())
    textview_traceback.set_cursor_visible(False)
    scroll_traceback = gtk.ScrolledWindow()
    scroll_traceback.set_shadow_type(gtk.SHADOW_IN)
    scroll_traceback.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    scroll_traceback.add(textview_traceback)
    scroll_traceback.set_size_request(-1, 300)
    button_report_bug = image_stock_button(gtk.STOCK_DIALOG_WARNING, _('Click here to report bug via web-page') )
    button_report_bug.connect('clicked', lambda w: report_bug() )
    button_close = image_stock_button(gtk.STOCK_CLOSE, _('Close'))
    button_close.connect('clicked', lambda w: dialog.destroy())
    bottom_box = gtk.HBox(False, 10)
    bottom_box.pack_start(button_report_bug, False)
    bottom_box.pack_start(button_close, False)
    
    dialog = gtk.Dialog(_('Bug appears!'), None, gtk.DIALOG_NO_SEPARATOR)
    dialog.set_border_width(10)
    dialog.vbox.set_spacing(5)
    dialog.vbox.pack_start(title_box, False)
    dialog.vbox.pack_start(scroll_traceback)
    dialog.vbox.show_all()
    
    dialog.action_area.pack_start(bottom_box, False)
    dialog.action_area.show_all()
    
    dialog.run()
    dialog.destroy()

sys.excepthook = exception_happened

class MainView:
    def __create_toolitem(self, icon, text, signal_name, callback, *callback_args):
        is_string_not_empty(icon)
        is_string_not_empty(text)
        is_string_not_empty(signal_name)
        assert callable(callback)
        
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(icon, 40, 40)
        image = gtk.image_new_from_pixbuf(pixbuf)
        align_image = gtk.Alignment(0.5, 0.5)
        align_image.add(image)
        align_image.set_size_request(65, -1)
        text = gtk.Label(text)
        import pango
        text.modify_font(pango.FontDescription('Sans 9'))
        text.set_alignment(0.5, 0.5)
        text.set_justify(gtk.JUSTIFY_CENTER)
        vbox = gtk.VBox(False, 5)
        vbox.pack_start(align_image)
        vbox.pack_start(text)
        button = gtk.Button()
        button.add(vbox)
        button.set_relief(gtk.RELIEF_NONE)
        button.connect(signal_name, callback, *callback_args)
        item = gtk.ToolItem()
        item.add(button)
        return item
    
    def add_buttons_in_toolbar(self):
        item_quit = self.__create_toolitem(D+'sora_icons/m_quit.png', _('Quit'), 'clicked', self.terminate_program)
        self.toolbar.insert(item_quit, 0)

        menu = load_others_menu(COMMON, DESKTOP, DISTRIBUTION, self)
        item = self.__create_toolitem(D+'sora_icons/m_others.png', _('Others'), 'button_release_event', self.__show_popupmenu_on_toolbaritem, menu)
        self.toolbar.insert(item, 0)
        menu = load_preferences_menu(COMMON, DESKTOP, DISTRIBUTION, self)
        item = self.__create_toolitem(D+'sora_icons/m_preference.png', _('Preferences'), 'button_release_event', self.__show_popupmenu_on_toolbaritem, menu)
        self.toolbar.insert(item, 0)
        menu = load_study_linux_menu(COMMON, DESKTOP, DISTRIBUTION, self)
        item = self.__create_toolitem(D+'sora_icons/m_study_linux.png', _('Study\nLinux'), 'button_release_event', self.__show_popupmenu_on_toolbaritem, menu)
        self.toolbar.insert(item, 0)

        List = [
                ('HardwareInfoPane', D+'sora_icons/m_hardware.png', _('Hardware\nInformation'), ),
                ('LinuxInfoPane', D+'sora_icons/m_linux.png', _('Linux\nInformation'), ),
                ('SystemSettingPane', D+'sora_icons/m_linux_setting.png', _('System\nSettings'), ),
                ('InstallRemovePane', D+'sora_icons/m_install_remove.png', _('Install\nSoftware'), ),
                ('UbuntuFastestMirrorPane', D+'sora_icons/m_fastest_repos.png', _('Fastest\nRepository'), ),
                ('UbuntuAPTRecoveryPane', D+'sora_icons/m_apt_recovery.png', _('Recover\nAPT'), ),
                ('CleanUpPane', D+'other_icons/m_clean_up.png', _('Clean up')),
                ]
        List.reverse()
        for name, icon, text in List:
            if not name in self.contents: continue
            item = self.__create_toolitem(icon, text, 'clicked', self.activate_pane, name)
            self.toolbar.insert(item, 0)
            last_name = name
        self.activate_pane(None, last_name) # automatically activate the left-most pane

    def __show_popupmenu_on_toolbaritem(self, widget, event, menu):
        if event.type == gtk.gdk.BUTTON_RELEASE and event.button == 1:
            menu.popup(None, None, None, event.button, event.time)
            return True
        return False

    def activate_pane(self, widget, name):
        assert isinstance(name, str)
        if name in self.contents:
            self.change_content_basic(name)

    def change_content_basic(self, name):
        assert isinstance(name, str)
        self.current_pane = name
        for child in self.toggle_area.get_children():
            self.toggle_area.remove(child)
        content = self.contents[name]
        self.toggle_area.add(content)
        self.toggle_area.show_all()

    def lock(self):
        self.stop_delete_event = True
        self.toolbar.set_sensitive(False)
    
    def unlock(self):
        self.stop_delete_event = False
        self.toolbar.set_sensitive(True)

    def terminate_program(self, *w):
        if self.stop_delete_event:
            return True
        
        from support.windowpos import WindowPos
        WindowPos.save(self.window,'main')
        
        for pane in self.contents.values():
            if hasattr(pane, 'save_state'):
                pane.save_state()

        gtk.main_quit()
        sys.exit()

    def show_day_tip(self, *w):
        from support.tipoftheday import TipOfTheDay
        w=TipOfTheDay()
        w.run()
        w.destroy()

    def register(self, pane):
        key = pane.__class__.__name__
        try:
            assert not '.' in key, key
            assert not key in self.contents, key
            self.contents[key] = pane
        except:
            import traceback
            traceback.print_exc()

    def __init__(self):
        self.app_classes = None
        self.window = None # MainView window
        self.stop_delete_event = False
        self.contents = {}
        
        self.toggle_area = gtk.VBox()
        self.toggle_area.set_border_width(5)
        
        vbox = gtk.VBox(False, 0)
        
        self.toolbar = gtk.Toolbar()
        self.toolbar.set_orientation(gtk.ORIENTATION_HORIZONTAL)
        self.toolbar.set_style(gtk.TOOLBAR_BOTH)
        vbox.pack_start(self.toolbar, False)
        
        vbox.pack_start(self.toggle_area, True, True)
        
        self.window = window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title('Ailurus ' + AILURUS_VERSION)
        window.connect("delete_event", self.terminate_program)
        window.add(vbox)

        from support.windowpos import WindowPos
        WindowPos.load(window,'main')

import common as COMMON
DESKTOP = get_desktop_environment()
DISTRIBUTION = get_distribution()
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

from optparse import OptionParser
parser = OptionParser(usage=_('usage: %prog [options]'))
parser.add_option('-f', action='store_false', dest='all', default=True, help=_('do not load all functionality'))
parser.add_option('--information', action='store_true', dest='information', default=False, help=_('load "information" functionality'))
parser.add_option('--system-setting', action='store_true', dest='system_setting', default=False, help=_('load "system setting" functionality'))
parser.add_option('--install-software', action='store_true', dest='install_software', default=False, help=_('load "install software" functionality'))
if getattr(DISTRIBUTION, '__name__') == 'ubuntu':
    parser.add_option('--fastest-repository', action='store_true', dest='fastest_repository', default=False, help=_('load "fastest repository" functionality'))
    parser.add_option('--apt-recovery', action='store_true', dest='apt_recovery', default=False, help=_('load "apt recovery" functionality'))
    parser.add_option('--clean-up', action='store_true', dest='clean_up', default=False, help=_('load "clean up" functionality'))
if getattr(DISTRIBUTION, '__name__') == 'fedora':
    parser.add_option('--rpm-recovery', action='store_true', dest='rpm_recovery', default=False, help=_('load "rpm recovery" functionality'))
options, args = parser.parse_args()

detect_running_instances()
change_task_name()
set_default_window_icon()
check_dbus_configuration()

# show splash window
from support.splashwindow import SplashWindow
splash = SplashWindow()
splash.show_all()
while gtk.events_pending(): gtk.main_iteration()

# load Linux skills
tips = load_tips(COMMON, DESKTOP, DISTRIBUTION)
import support.tipoftheday
support.tipoftheday.tips = tips

# load main window
main_view = MainView()

if options.system_setting or options.all:
    splash.add_text(_('<span color="grey">Loading system settings pane ... </span>\n'))
    items = load_setting(COMMON, DESKTOP, DISTRIBUTION)
    from system_setting_pane import SystemSettingPane
    pane = SystemSettingPane(items)
    main_view.register(pane)

if getattr(DISTRIBUTION, '__name__') == 'ubuntu':
    if options.fastest_repository or options.all:
        from ubuntu.fastest_mirror_pane import UbuntuFastestMirrorPane
        pane = UbuntuFastestMirrorPane(main_view)
        main_view.register(pane)

    if options.apt_recovery or options.all:
        from ubuntu.apt_recovery_pane import UbuntuAPTRecoveryPane
        pane = UbuntuAPTRecoveryPane(main_view)
        main_view.register(pane)

    if options.clean_up or options.all:
        from ubuntu.clean_up_pane import CleanUpPane
        pane = CleanUpPane(main_view)
        main_view.register(pane)

if getattr(DISTRIBUTION, '__name__') == 'fedora':
    if options.rpm_recovery or options.all:
        from rpm_recovery_pane import FedoraRPMRecoveryPane
        pane = FedoraRPMRecoveryPane(main_view)
        main_view.register(pane)

if options.information or options.all:
    splash.add_text(_('<span color="grey">Loading information pane ... </span>\n'))
    hwinfo = load_hardwareinfo(COMMON, DESKTOP, DISTRIBUTION)
    from info_pane import HardwareInfoPane
    pane = HardwareInfoPane(main_view, hwinfo)
    main_view.register(pane)

    linuxinfo = load_linuxinfo(COMMON, DESKTOP, DISTRIBUTION)
    from info_pane import LinuxInfoPane
    pane = LinuxInfoPane(main_view, linuxinfo)
    main_view.register(pane)

if options.install_software or options.all:
    splash.add_text(_('<span color="grey">Loading applications pane ... </span>\n'))
    
    wait_firefox_to_create_profile()
    
    if getattr(DISTRIBUTION, '__name__') == 'ubuntu':
        APT.refresh_cache()
    elif getattr(DISTRIBUTION, '__name__') == 'fedora':
        RPM.refresh_cache()
    
    app_classes = load_app_classes(COMMON, DESKTOP, DISTRIBUTION)
    main_view.app_classes = app_classes
    custom_app_classes = load_custom_app_classes()
    from install_remove_pane import InstallRemovePane
    pane = InstallRemovePane(main_view, app_classes + custom_app_classes)
    main_view.register(pane)
    main_view.install_remove_pane = pane

main_view.add_buttons_in_toolbar()
main_view.window.show_all()
splash.destroy()
# do not show tip of the day
# if not Config.get_disable_tip():
#    main_view.show_day_tip()

# all right
gtk.gdk.threads_init()
gtk.gdk.threads_enter()
gtk.main()
gtk.gdk.threads_leave()
sys.exit()
