# Waydroid Injector

Inject custom content described in a manifest into waydroid's data.

## Requirements:

- Python >= 3.12
- Waydroid with overlay enabled
- Root privilege

### How to check Waydroid

Check `waydroid` section for key `mount_overlays` in `/var/lib/waydroid/waydroid.cfg`.
Most of newly initialized installations of waydroid should have enabled this automatically.
Remove `/var/lib/waydroid` and init waydroid again if not enabled.

## Install

Run [install.sh](./install.sh), environment variables `DESTDIR` and `PREFIX` can be used for customizing installation path.
`PREFIX` defaults to `$HOME/.local`.

## Usage:

```
$ ./waydroid-injector --help
usage: waydroid-injector [-h] [-v] [-d] [-e] [-s DESTDIR] {install,uninstall} ...

Inject custom content described in a manifest into waydroid's data.

positional arguments:
  {install,uninstall}
    install             Install the manifest into waydroid's data.
    uninstall           Uninstall the manifest from waydroid's data.

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -d, --dry-run         skip actual changes.
  -e, --debug           enable debug mode.
  -s DESTDIR, --destdir DESTDIR
                        destination to rootfs.

```

## Manifest

See [example](./manifest-example.toml)

## Notes:

1. This script does not record which manifest the file belongs to, for example, if you have installed `manifest-a.toml` and `manifest-b.toml`,
both of them have a `/var/lib/waydroid/overlay/example.file` in contents, after you installed `manifest-b.toml`,
the file created by `manifest-a.toml` will be replaced with the one from `manifest-b.toml`. If you uninstall `manifest-a.toml` after this,
the file created by `manifest-b.toml` will also be removed.
