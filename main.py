import asyncio
import os
import platform
import re
import shutil
import tempfile

import decky

GAMES = {
    39210: "FINAL FANTASY XIV Online",
    312060: "FINAL FANTASY XIV Online Free Trial",
}

# XLM's own name for its compatibility tool (static/compatibilitytool.vdf in Blooym/xlm).
TOOL_NAME = "xlm"
TOOL_DIR = "XLM"
# Steam's name for the tool once this plugin installed it, so it can be told from a manual install.
DISPLAY_NAME = "XLCore [XLM Decky]"

UPSTREAM = "https://github.com/Blooym/xlm/releases/latest/download"
# XLM and XIVLauncher.Core have no aarch64 builds upstream yet; this fork publishes them.
ARM64_RELEASE = "https://github.com/PofMagicfingers/XIVLauncher.Core/releases/latest/download"


def arch():
    machine = platform.machine().lower()
    return "aarch64" if machine in ("aarch64", "arm64") else machine


def source():
    """Where XLM comes from on this machine: (xlm binary URL, extra launch arguments)."""
    args = "--run-as-steam-compat-tool=true --use-fallback-secret-provider"
    if arch() == "aarch64":
        return (
            f"{ARM64_RELEASE}/xlm-aarch64",
            f"{args} --xlcore-web-release-url {ARM64_RELEASE}/ --aria-source url:{ARM64_RELEASE}/aria2c-arm64.tar.gz",
        )
    return f"{UPSTREAM}/xlm-x86_64-unknown-linux-gnu", args


def steam_root():
    home = decky.DECKY_USER_HOME
    for path in (os.path.join(home, ".steam", "root"), os.path.join(home, ".local", "share", "Steam")):
        if os.path.isdir(os.path.join(path, "steamapps")):
            return os.path.realpath(path)
    return None


def libraries(root):
    found = [root]
    try:
        with open(os.path.join(root, "steamapps", "libraryfolders.vdf"), encoding="utf-8") as vdf:
            found += re.findall(r'^\s*"path"\s*"(.*)"\s*$', vdf.read(), re.MULTILINE)
    except OSError:
        pass
    return list(dict.fromkeys(found))


def game_state(root, appid):
    """'installed', 'installing' or None, from the app manifest in any library."""
    for library in libraries(root):
        manifest = os.path.join(library, "steamapps", f"appmanifest_{appid}.acf")
        try:
            with open(manifest, encoding="utf-8") as acf:
                flags = re.search(r'"StateFlags"\s*"(\d+)"', acf.read())
        except OSError:
            continue
        # StateFlags 4 is "fully installed"; other values are downloads, updates or validations in progress.
        return "installed" if flags and int(flags.group(1)) == 4 else "installing"
    return None


def compat_tool(root, appid):
    """The compatibility tool Steam last saved for the app, from config.vdf (written by Steam on exit)."""
    try:
        with open(os.path.join(root, "config", "config.vdf"), encoding="utf-8") as vdf:
            text = vdf.read()
    except OSError:
        return None
    start = text.find('"CompatToolMapping"')
    if start < 0:
        return None
    start = text.find("{", start)
    depth, end = 0, start
    for end in range(start, len(text)):
        depth += {"{": 1, "}": -1}.get(text[end], 0)
        if depth == 0:
            break
    entry = re.search(rf'"{appid}"\s*\{{[^}}]*?"name"\s*"([^"]*)"', text[start:end])
    return entry.group(1) if entry else None


def steam_started_at():
    """When the Steam client process started (seconds since the epoch), or None."""
    try:
        with open("/proc/stat") as stat:
            boot = next(int(line.split()[1]) for line in stat if line.startswith("btime "))
        tick = os.sysconf("SC_CLK_TCK")
        starts = []
        for pid in filter(str.isdigit, os.listdir("/proc")):
            try:
                with open(f"/proc/{pid}/comm") as comm:
                    if comm.read().strip() != "steam":
                        continue
                with open(f"/proc/{pid}/stat") as stat:
                    fields = stat.read().rsplit(")", 1)[1].split()
                starts.append(boot + int(fields[19]) / tick)
            except (OSError, IndexError, ValueError):
                continue
        return min(starts) if starts else None
    except (OSError, StopIteration, ValueError):
        return None


def fresh_install_marker():
    return os.path.join(decky.DECKY_PLUGIN_SETTINGS_DIR, "fresh-install")


def restart_needed():
    """Steam lists a compatibility tool installed while it runs only after a restart."""
    try:
        installed_at = os.path.getmtime(fresh_install_marker())
    except OSError:
        return False
    started = steam_started_at()
    if started is not None and started > installed_at:
        os.remove(fresh_install_marker())
        return False
    return True


def set_display_name(tool_dir):
    vdf = os.path.join(tool_dir, "compatibilitytool.vdf")
    with open(vdf, encoding="utf-8") as f:
        text = f.read()
    with open(vdf, "w", encoding="utf-8") as f:
        f.write(re.sub(r'("display_name"\s*)"[^"]*"', rf'\1"{DISPLAY_NAME}"', text))


def subprocess_env():
    # Decky's bundled Python sets LD_LIBRARY_PATH for itself, which breaks system programs.
    env = dict(os.environ)
    env.pop("LD_LIBRARY_PATH", None)
    env["HOME"] = decky.DECKY_USER_HOME
    return env


async def run(*cmd):
    process = await asyncio.create_subprocess_exec(
        *cmd, env=subprocess_env(), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    out, _ = await process.communicate()
    text = out.decode(errors="replace").strip()
    if process.returncode != 0:
        raise RuntimeError(f"{os.path.basename(cmd[0])} failed ({process.returncode}): {text[-500:]}")
    return text


class Plugin:
    async def status(self):
        root = steam_root()
        tool = os.path.join(root, "compatibilitytools.d", TOOL_DIR) if root else None
        installed = bool(tool) and os.path.isfile(os.path.join(tool, "xlm")) and os.path.isfile(
            os.path.join(tool, "compatibilitytool.vdf"))
        return {
            "arch": arch(),
            "source": source()[0],
            "steamRoot": root,
            "xlmInstalled": installed,
            "restartNeeded": installed and restart_needed(),
            "toolName": TOOL_NAME,
            "games": [
                {
                    "appid": appid,
                    "name": name,
                    "state": game_state(root, appid) if root else None,
                    "compatTool": compat_tool(root, appid) if root else None,
                }
                for appid, name in GAMES.items()
            ],
        }

    async def install_xlm(self):
        root = steam_root()
        if not root:
            raise RuntimeError("Steam's folder was not found")
        compat = os.path.join(root, "compatibilitytools.d")
        url, launch_args = source()
        decky.logger.info(f"Installing XLM from {url}")

        with tempfile.TemporaryDirectory() as tmp:
            xlm = os.path.join(tmp, "xlm")
            await run("curl", "--fail", "--silent", "--show-error", "--location", "--max-time", "300", "-o", xlm, url)
            os.chmod(xlm, 0o755)

            # Keep the user's XLM pre- and post-launch scripts across reinstalls.
            current = os.path.join(compat, TOOL_DIR)
            fresh = not os.path.isfile(os.path.join(current, "compatibilitytool.vdf"))
            hooks = os.path.join(tmp, "hooks")
            os.makedirs(hooks)
            for name in ("prelaunch.d", "postlaunch.d"):
                if os.path.isdir(os.path.join(current, name)):
                    shutil.copytree(os.path.join(current, name), os.path.join(hooks, name), symlinks=True)
            shutil.rmtree(current, ignore_errors=True)
            os.makedirs(compat, exist_ok=True)

            await run(xlm, "install-steam-tool", "--xlm-updater-disable",
                      f"--extra-launch-args={launch_args}", "--steam-compat-path", compat + "/")
            shutil.copytree(hooks, current, symlinks=True, dirs_exist_ok=True)
            set_display_name(current)

        if fresh:
            os.makedirs(decky.DECKY_PLUGIN_SETTINGS_DIR, exist_ok=True)
            open(fresh_install_marker(), "w").close()

        decky.logger.info("XLM installed")
        return await self.status()

    async def _main(self):
        decky.logger.info(f"XLM setup loaded ({arch()})")

    async def _unload(self):
        pass
