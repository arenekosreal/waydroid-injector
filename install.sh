#!/usr/bin/bash

# DESTDIR=/custom/path
# PREFIX=/usr
# Install everything under /custom/path/usr
declare slash="$DESTDIR${PREFIX:-$HOME/.local}"

declare files
declare file

for file in manifests/*.toml
do
    echo "Installing $file to $slash/share/waydroid-injector/$file..."
    install -Dvm644 "$file" "$slash/share/waydroid-injector/$file"
    files="$files\n$slash/share/waydroid-injector/$file"
done
files="$files\n$slash/share/waydroid-injector"

echo "Installing documents..."
install -Dvm644 manifest-example.toml "$slash/share/doc/waydroid-injector/manifest-example.toml"
files="$files\n$slash/share/doc/waydroid-injector/manifest-example.toml\n$slash/share/doc/waydroid-injector"

echo "Installing main script..."
install -Dvm755 waydroid-injector "$slash/bin/waydroid-injector"
files="$files\n$slash/bin/waydroid-injector"

echo "To uninstall, remove those file(s) and folder(s):"
echo -e "$files"
