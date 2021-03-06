#!/bin/bash
#
# Polychromatic is free software: you can redistribute it and/or modify
# it under the temms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Polychromatic is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Polychromatic. If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2016 Luke Horwell <lukehorwell37+code@gmail.com>
#
############################################################################
# This script manually deletes the Polychromatic and Python
# libraries from the system.
############################################################################

# Paths
target_data="/usr/share/polychromatic"
target_bin="/usr/bin"
target_icon="/usr/share/icons"
modules="/usr/lib/python3/dist-packages/polychromatic"

# Are we root?
if [ "$(id -u)" != "0" ]; then
    echo "To uninstall, this script must be run as root." 1>&2
    exec sudo "$0"
    exit
fi

# If a clean removal script is present, run that instead.
clean_script="$target_data/uninstall-polychromatic.sh"
if [ ! "$0" == "$clean_script" ]; then
    if [ -f "$clean_script" ]; then
        echo "Cleanly removing the software from your system..."
        exec "$clean_script"
    fi
fi

# Deleting files
rm -rf "$target_data"
rm -rf "$modules"
rm     "$target_bin/polychromatic-controller"
rm     "$target_bin/polychromatic-tray-applet"
rm     "$target_icon/hicolor/scalable/apps/polychromatic.svg"
rm -rf /usr/share/applications/polychromatic-controller.desktop
rm -rf /usr/share/applications/polychromatic-tray.desktop

# Post removal
update-icon-caches /usr/share/icons/hicolor/

# Success!
echo "Uninstall Success!"
exit 0

