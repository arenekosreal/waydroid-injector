# Waydroid Injector

Inject custom content described in a manifest into waydroid's data.

## Features:

- No need to modify `system.img` or `vendor.img` to inject your content.

## Requirements:

- Python >= 3.12

- Waydroid with overlay enabled

- Root privilege

### How to check Waydroid

Check `waydroid` section for key `mount_overlays` in `/var/lib/waydroid/waydroid.cfg`.
Most of newly initialized installations of waydroid should have enabled this automatically.
Remove `/var/lib/waydroid` and init waydroid again if not enabled.

> [!NOTE]
> Removing `/var/lib/waydroid` and initializing waydroid again should not destroy your user data.
As it is usually storaged at `${XDG_DATA_HOME:-$HOME/.local/share}/waydroid/data`.

## Install

1. [Build](#build) or download wheel from [Release](https://github.com/arenekosreal/waydroid-injector/releases)

2. Install the wheel, see [here](https://pip.pypa.io/en/stable/user_guide/#installing-from-wheels) if you need help.

## Build

1. Insall pdm. See [here](https://pdm-project.org/en/stable/#installation) if you need help.

2. Install dependencies. Run `pdm install` to install them. If you need to run tests, run `pdm install --dev` instead.

3. Build. Run `pdm build` in the repository.

4. Get wheel. Go to `dist` folder and you will find wheel file.

## Test

This is optional, run `pdm run pytest` and we will check code with tests defined in [tests](./tests) folder and ruff.
You need to run `pdm install --dev` in Step 2 of [Build](#build) to install extra dependencies required by testing.

## Run

After you [Install](#install)ed this package, you will find a new command `waydroid-injector` available in your `PATH`.
You can also choose to run this project directly, running directly does not need install wheel, but this is just for test purpose.
If you still need run this project directly, simply run `pdm run waydroid-injector` should be fine.

## Usage:

```
$ pdm run waydroid-injector --help
usage: waydroid-injector [-h] [-v] [-d] [-e] [-s DESTDIR] {install,uninstall} ...

Inject custom content described in a manifest into waydroid's data.

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -d, --dry-run         install contents into ./slash directory.
  -e, --debug           enable debug mode.
  -s DESTDIR, --destdir DESTDIR
                        destination to rootfs.

operations:
  available operations:

  {install,uninstall}
    install             Install the manifest into waydroid's data.
    uninstall           Uninstall the manifest from waydroid's data.

```

## Manifest

See [example](./manifest-example.toml) and [manifests](./manifests).

## Notes:

1. This script does not record which manifest the file belongs to, for example, if you have installed `manifest-a.toml` and `manifest-b.toml`,
both of them have a `/var/lib/waydroid/overlay/example.file` in contents, after you installed `manifest-b.toml`,
the file created by `manifest-a.toml` will be replaced with the one from `manifest-b.toml`. If you uninstall `manifest-a.toml` after this,
the file created by `manifest-b.toml` will also be removed.
