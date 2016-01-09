#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#
# Chroma Config Tool is free software: you can redistribute it and/or modify
# it under the temms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Chroma Config Tool is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Chroma Config Tool. If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2015-2016 Luke Horwell <lukehorwell37+code@gmail.com>
#

import os, sys, signal, inspect
from gi.repository import Gtk, Gdk, WebKit
import daemon_dbus

# Default Settings & Preferences
rgb_effects_red = 0;
rgb_effects_green = 255;
rgb_effects_blue = 0;
current_effect = 'custom';
layout = 'en-gb';

class Paths():
    # Initializes paths and directories

    ## Where are we?
    location = os.path.dirname( os.path.abspath(inspect.getfile(inspect.currentframe())) )
    location_data = os.path.join(location, 'data/')
    location_installed = '/usr/share/razer_chroma_controller'

    ## Where user's configuration is saved
    save_root = os.path.expanduser('~') + '/.config/razer_chroma'
    save_profiles = save_root + '/profiles'
    save_backups = save_root + '/backups'

    ## Check 'data' folder exists.
    if ( os.path.exists(location_data) == False ):
        print('Data folder is missing. Exiting.')
        exit()

    ## Check we have a folder to save data (eg. profiles)
    if ( os.path.exists(save_root) == False ):
        print('Configuration folder does not exist. Creating',save_root,)
        os.makedirs(save_root)
        os.makedirs(save_profiles)
        os.makedirs(save_backups)

    # Does the 'dynamic' binary exist? (required for key profiles)
    ### In same folder as script.
    if os.path.exists(location + '/dynamic') == True:
        dynamicPath = location + '/dynamic'
    ### Compiled in Git project 'examples' folder
    elif os.path.exists(location + '/../../examples/dynamic') == True:
        dynamicPath = location + '/../../examples/dynamic'
    else:
        dynamicPath = 'notfound'

    ## Is a sudoers file present for the utility?
    ## (This bypasses the password authentication prompt on Ubuntu/Debian distros and
    ##  assumes the application is installed to the system)
    if os.path.exists('/etc/sudoers.d/razer_chroma_dynamic') == True:
        dynamicPath = '/usr/share/razer_chroma_controller/dynamic'
        dynamicExecType = 'sudoers'
    else:
        dynamicExecType = 'pkexec'

class ChromaController(object):
    ##################################################
    # Page Switcher
    ##################################################
    def show_menu(self, page):
        print("Opening menu '"+page+"'")

        # Hide all footer buttons
        webkit.execute_script('$("#retry").hide()')
        webkit.execute_script('$("#edit-save").hide()')
        webkit.execute_script('$("#edit-preview").hide()')
        webkit.execute_script('$("#cancel").hide()')
        webkit.execute_script('$("#close-window").hide()')
        webkit.execute_script('$("#pref-open").hide()')
        webkit.execute_script('$("#pref-save").hide()')

        if page == 'main_menu':
            webkit.execute_script('changeTitle("Configuration Menu")')
            webkit.execute_script('smoothFade(".menu_area",'+page+')')
            webkit.execute_script('$("#close-window").show()')
            webkit.execute_script('$("#pref-open").show()')
            self.refreshProfilesList()

        elif page == 'not_detected':
            webkit.execute_script('changeTitle("Keyboard Not Detected")')

        elif page == 'profile_editor':
            global profileName
            webkit.execute_script('changeTitle("Edit '+profileName+'")')
            webkit.execute_script('smoothFade("#main_menu","#profile_editor")')
            webkit.execute_script('$("#cancel").show()')
            webkit.execute_script('$("#edit-preview").show()')
            webkit.execute_script('$("#edit-save").show()')

        elif page == 'preferences':
            webkit.execute_script('changeTitle("Preferences")')
            webkit.execute_script('$("#cancel").show()')
            webkit.execute_script('$("#pref-save").show()')

        else:
            print("Unknown menu '"+page+"'!")

    ##################################################
    # Page Initialization
    ##################################################
    def page_loaded(self, WebView, WebFrame):
        # Check if the Chroma is plugged in as soon as the page finishes loading.
        print("Detecting Chroma Keyboard... ", end='')
        # FIXME: NOT YET IMPLEMENTED
        # print('found at ####')
        print("\nfixme: page_loaded detect chroma keyboard")
        #  -- If it is, show the main menu.
        # --  If not, kindly ask the user to do so.
        self.show_menu('main_menu')

        # Load profiles and preferences
        # FIXME: Not yet implemented!
        #~ self.preferences('load')

        webkit.execute_script('instantProfileSwitch = false;'); # Unimplemented instant profile change option.
        webkit.execute_script("$('#profiles-activate').show()");

        # Load list of profiles
        self.refreshProfilesList()

        # Apply preferences
        ## FIXME: Unimplemented: Default starting colour.
        #~ webkit.execute_script('$("#rgb_effects_preview").css("background-color","rgba('+str(rgb_effects_red)+','+str(rgb_effects_green)+','+str(rgb_effects_blue)+',1.0)")')

        ## Write keyboard
        global layout
        keyboardLayoutFile = open(Paths.location_data+'/layouts/'+layout+'.html','r')
        for line in keyboardLayoutFile:
          if '\n' == line[-1]:
            webkit.execute_script("$('#keyboard').append('"+line.split('\n')[0]+"')")
        print("Loaded keyboard layout '"+layout+"'")

        # Does 'dynamic' exist? Without this, profiles can't be activated!
        # See '/../examples/dynamic-examples/readme' for more details.
        # If this is integrated to dbus, this external binary won't be needed (nor require root privileges to execute)
        if Paths.dynamicPath == 'notfound':
            webkit.execute_script('$("#profiles-activate").')
            print("WARNING: Binary for 'dynamic' not found!")
            print("         You won't be able to activate any key profiles created with the utility without compiling the program and placing beside this script.")
            print("         See '/../examples/dynamic-examples/readme' for details about 'dynamic'.")

    def refreshProfilesList(self):
        global webkit
        webkit.execute_script('$("#profiles_list").html("")')
        for profile in ChromaProfiles.getFileList():
            item = "<option value='"+profile+"'>"+profile+"</option>"
            webkit.execute_script('$("#profiles_list").append("'+item+'")')

    ##################################################
    # Commands
    ##################################################
    def process_uri(self, view, frame, net_req, nav_act, pol_dec):
        uri = net_req.get_uri()
        frame.stop_loading()

        if uri.startswith('cmd://'):
            command = uri[6:]
            print("Command: '"+command+"'")
            self.process_command(command)

        if uri.startswith('web://'):
            webURL = uri[6:]
            print('fixme:open web browser to URL')

    def process_command(self, command):
        global rgb_effects_red, rgb_effects_green, rgb_effects_blue, current_effect
        global profileName, profileMemory
        global webkit

        if command == 'quit':
            quit()

        ## Effects & Keyboard Controls
        elif command.startswith('brightness'):
            value = int(command[11:])
            daemon.SetBrightness(value)

        elif command.startswith('effect'):
            if command == 'effect-none':
                current_effect = "none"
                daemon.SetEffect('none')
                webkit.execute_script('$("#rgb_effects").fadeOut("fast")')
                webkit.execute_script('$("#waves").fadeOut("fast")')

            elif command == 'effect-spectrum':
                current_effect = "spectrum"
                daemon.SetEffect('spectrum')
                webkit.execute_script('$("#rgb_effects").fadeOut("fast")')
                webkit.execute_script('$("#waves").fadeOut("fast")')

            elif command.startswith('effect-wave'):
                current_effect = "wave"
                daemon.SetEffect('wave',int(command[12:])) # ?1 or ?2 for direction
                webkit.execute_script('smoothFade("#rgb_effects","#waves")')

            elif command == 'effect-reactive':
                current_effect = "reactive"
                daemon.SetEffect('reactive', rgb_effects_red, rgb_effects_green, rgb_effects_blue)
                webkit.execute_script('smoothFade("#waves","#rgb_effects")')

            elif command == 'effect-breath':
                current_effect = "breath"
                daemon.SetEffect('breath', rgb_effects_red, rgb_effects_green, rgb_effects_blue)
                webkit.execute_script('smoothFade("#waves","#rgb_effects")')

            elif command == 'effect-static':
                current_effect = "static"
                daemon.SetEffect('static', rgb_effects_red, rgb_effects_green, rgb_effects_blue)
                webkit.execute_script('smoothFade("#waves","#rgb_effects")')

        elif command == 'enable-marco-keys':
            daemon.MarcoKeys(True)
            webkit.execute_script('$("#marco-keys-enable").addClass("btn-disabled")')
            webkit.execute_script('$("#marco-keys-enable").html("Marco Keys In Use")')

        elif command == 'gamemode-enable':
            daemon.GameMode(True)
            webkit.execute_script('$("#game-mode-status").html("Enabled")')
            webkit.execute_script('$("#game-mode-enable").hide()')
            webkit.execute_script('$("#game-mode-disable").show()')

        elif command == 'gamemode-disable':
            daemon.GameMode(False)
            webkit.execute_script('$("#game-mode-status").html("Disabled")')
            webkit.execute_script('$("#game-mode-enable").show()')
            webkit.execute_script('$("#game-mode-disable").hide()')

        ## Changing colours for this session.
        elif command.startswith('ask-color') == True:
            colorseldlg = Gtk.ColorSelectionDialog("Choose a colour")
            colorsel = colorseldlg.get_color_selection()

            if colorseldlg.run() == Gtk.ResponseType.OK:
                color = colorsel.get_current_color()
                red = int(color.red / 256)
                green = int(color.green / 256)
                blue = int(color.blue / 256)
                element = command.split('?')[1]
                command = 'set-color?'+element+'?'+str(red)+'?'+str(green)+'?'+str(blue)
                self.process_command(command)

            colorseldlg.destroy()

        elif command.startswith('set-color') == True:
            # Expects 4 parameters separated by '?' in order: element, red, green, blue (RGB = 0-255)
            colors = command.split('set-color?')[1]
            element = colors.split('?')[0]
            red = int(colors.split('?')[1])
            green = int(colors.split('?')[2])
            blue = int(colors.split('?')[3])
            print("Set colour to: RGB("+str(red)+", "+str(green)+", "+str(blue)+")")
            webkit.execute_script('$("#'+element+'_preview").css("background-color","rgba('+str(red)+','+str(green)+','+str(blue)+',1.0)")')

            # Update global variables if applicable
            if element == 'rgb_effects':    # Static effect colours
                rgb_effects_red = red
                rgb_effects_green = green
                rgb_effects_blue = blue
            elif element == 'rgb_tmp':      # Temporary colour while editing profiles.
                rgb_edit_red = red
                rgb_edit_green = green
                rgb_edit_blue = blue

            # Update static colour effects if currently in use.
            if current_effect == 'static':
                self.process_command('effect-static')
            elif current_effect == 'breath':
                self.process_command('effect-breath')
            elif current_effect == 'reactive':
                self.process_command('effect-reactive')
            webkit.execute_script('$("#rgb_effects").fadeIn()')

        ## Opening different pages
        elif command == 'cancel-changes':
            self.show_menu('main_menu')

        elif command == 'pref-open':
            self.preferences('load')
            self.show_menu('preferences')

        elif command == 'pref-save':
            self.preferences('save')
            self.show_menu('main_menu')

        elif command.startswith('profile-edit') == True:
            profileName = command.split('profile-edit?')[1].replace('%20',' ')
            profilePath = Paths.save_profiles+'/'+profileName

            # Dynamic Profile File Format:
            #   <cmd> <parm>
            #   1 <x> <y> <red> <green> <blue>
            # File MUST end with '0'.

            # Profile Memory within Python
            # [ mode, x. y. red. green. blue ]
            # Mode = 1 = static key at X,Y

            # Clear any existing colours / array memory
            cleared_text = 'rgb(128,128,128)'
            cleared_border = 'rgb(70,70,70)'
            profileMemory = []

            for posX in range(0,21):
              for posY in range(0,5):
                webkit.execute_script('$("#x'+str(posX)+'-y'+str(posY)+'").css("border","2px solid '+cleared_border+'")')
                webkit.execute_script('$("#x'+str(posX)+'-y'+str(posY)+'").css("color","'+cleared_text+'")')

            try:
              with open(profilePath,'r') as f:
                  profileContents = f.read().splitlines()

              # Load new values
              for line in profileContents:
                if line != '0':
                  posX = line.split(' ')[1]
                  posY = line.split(' ')[2]
                  red = line.split(' ')[3]
                  green = line.split(' ')[4]
                  blue = line.split(' ')[5]
                  rgbCSS = 'rgb('+red+','+green+','+blue+')'
                  webkit.execute_script('$("#x'+posX+'-y'+posY+'").css("border","2px solid '+rgbCSS+'")')
                  webkit.execute_script('$("#x'+posX+'-y'+posY+'").css("color","'+rgbCSS+'")')
                  profileMemory.append([1, int(posX), int(posY), int(red), int(green), int(blue)])

              print('Opened profile "'+profileName+'"')
              self.show_menu('profile_editor')

            except:
              print('Problem opening "'+profilePath+'" for reading.')

        elif command.startswith('set-key') == True:
            # Replace any existing occurances first
            self.process_command('clear-key?'+command.split('set-key?')[1])

            # Parse position/colour information
            command = command.replace('%20',' ')
            posX = command.split('?')[1].strip('x').split('-')[0]
            posY = command.split('?')[1].split('-y')[1]
            color = command.split('?')[2]
            red = int(color.strip('rgb()').split(',')[0])
            green =int(color.strip('rgb()').split(',')[1])
            blue = int(color.strip('rgb()').split(',')[2])

            # Write to memory
            profileMemory.append([1, posX, posY, red, green, blue])

        elif command.startswith('clear-key') == True:
            command = command.replace('%20',' ')
            posX = command.split('?')[1].strip('x').split('-')[0]
            posY = command.split('?')[1].split('-y')[1]

            # Scan the profile in memory and erase any reference to it.
            row = 0
            for line in profileMemory:
              if str(line).startswith('[1, '+posX+", "+posY+",") == True:
                  del profileMemory[row]
              row = row + 1

        elif command.startswith('profile-activate') == True:
            command = command.replace('%20',' ')
            profileName = command.split('profile-activate?')[1]
            webkit.execute_script('setCursor("wait")')
            ChromaProfiles.setProfile('file',profileName)
            webkit.execute_script('$("#custom").html("Profile - '+profileName+'")')
            webkit.execute_script('$("#custom").prop("checked", true)')
            webkit.execute_script('setCursor("normal")')

        elif command.startswith('profile-del') == True:
            # TODO: Instead of JS-based prompt, use PyGtk or within web page interface?
            profileName = command.split('?')[1].replace('%20',' ')
            os.remove(Paths.save_profiles+'/'+profileName)
            print('Deleted profile: '+Paths.save_profiles+'/'+profileName)
            if os.path.exists(Paths.save_backups+'/'+profileName) == True:
                os.remove(Paths.save_backups+'/'+profileName)
                print('Deleted backup copy: '+Paths.save_backups+'/'+profileName)
            print('Forcing refresh of profiles list...')
            self.refreshProfilesList()

        elif command.startswith('profile-new') == True:
            # TODO: Instead of JS-based prompt, use PyGtk or within web page interface?
            profileName = command.split('?')[1].replace('%20',' ')
            profileMemory = []
            self.show_menu('profile_editor')

        elif command == 'profile-save':
            print('Saving profile "'+profileName+'...')
            profilePath = Paths.save_profiles + '/' + profileName

            # Backup if it's an existing copy, then erase original copy.
            if os.path.exists(profilePath) == True:
                os.rename(profilePath, Paths.save_backups+'/'+profileName)

            # Prepare to write to file
            profileSave = open(profilePath, "w")

            for line in profileMemory:
                lineBuffer=''
                for data in line:
                    lineBuffer = lineBuffer + str(data) + ' '

                profileSave.write(str(lineBuffer+'\n'))

            # Line must end with a zero ('0') to tell 'dynamic' this is the EOF.
            profileSave.write('0')
            profileSave.close()
            print('Saved to "'+profilePath+'".')
            self.show_menu('main_menu')

        else:
            print("         ... unimplemented!")

    ##################################################
    # Preferences
    ##################################################
    # Load or save preferences?
    def preferences(self, action):

        # FIXME: Incomplete
        return


    ##################################################
    # Initialization
    ##################################################
    def __init__(self):
        w = Gtk.Window(title="Razer BlackWidow Chroma Configuration")
        w.set_wmclass('razer_bcd_utility', 'razer_bcd_utility')
        w.set_position(Gtk.WindowPosition.CENTER)
        w.set_size_request(900, 600)
        w.set_resizable(False)
        w.set_icon_from_file(os.path.join(Paths.location_data, 'img/app-icon.svg'))
        w.connect("delete-event", Gtk.main_quit)

        # Create WebKit Container
        global webkit
        webkit = WebKit.WebView()
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.add(webkit)

        # Build an auto expanding box and add our scrolled window
        b = Gtk.VBox(homogeneous=False, spacing=0)
        b.pack_start(sw, expand=True, fill=True, padding=0)
        w.add(b)

        # Disable right click context menu
        webkit.props.settings.props.enable_default_context_menu = False

        # Load page
        webkit.open(os.path.join(Paths.location_data, 'chroma_controller.html'))

        # Process pages once they fully load.
        webkit.connect('load-finished',self.page_loaded)

        # Process any commands from the web page.
        webkit.connect('navigation-policy-decision-requested', self.process_uri)

        # Show the window.
        w.show_all()
        Gtk.main()

class ChromaProfiles():
    ##################################################
    # Profile Creation
    ##################################################
    # Print the file names of existing profiles.
    # Requires 'Paths' class.

    def getFileList():
        return os.listdir(Paths.save_profiles)


    def setProfile(source='memory', profileName=None):
        print("Applying profile '"+profileName+"' ... ",end='')
        global profileMemory
        if Paths.dynamicExecType == 'sudoers':
          print("using 'sudo' as sudoers file was detected.")
          print('---[ Dynamic Output ]-----------------------')
          if source == 'file':
            os.system('cat "' + Paths.save_profiles + '/' + profileName + '" |  sudo ' + Paths.dynamicPath)
          elif source == 'memory':
            os.system('echo "' + profileMemory + '" |  sudo ' + Paths.dynamicPath)
          print('\n--------------------------------------------')

        elif Paths.dynamicExecType == 'pkexec':
          print("using an authentication prompt to execute 'dynamic' with higher privileges to send data directly to the keyboard.")
          print('---[ Dynamic Output ]-----------------------')
          os.system('echo "' + profileMemory+ '" |  pkexec ' + Paths.dynamicPath)
          print('\n--------------------------------------------')


if __name__ == "__main__":
    # Kill the process when CTRL+C'd.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Connect to the DBUS daemon and determine paths.
    daemon = daemon_dbus.DaemonInterface()
    Paths()

    # Show Time!
    utilty = ChromaController()