# XLM Setup

A [Decky Loader](https://github.com/SteamDeckHomebrew/decky-loader) plugin that sets up
[XIVLauncher](https://github.com/goatcorp/XIVLauncher.Core) for FINAL FANTASY XIV through
[XLM](https://github.com/Blooym/xlm), from Steam's game mode:

1. Finds the full game (39210) or the free trial (312060) in the Steam libraries, and offers to
   install one when neither is there.
2. Installs XLM as a Steam compatibility tool, keeping its `prelaunch.d` and `postlaunch.d` hooks.
3. Sets XLM as the game's compatibility tool (after a Steam restart, the first time) and launches it.

XLM comes from Blooym/xlm's releases on x86_64 (Steam Deck). On aarch64 (Steam on Android through
[DroidDeck](https://github.com/Droid-Deck/DroidDeck)) it comes from
[PofMagicfingers/XIVLauncher.Core](https://github.com/PofMagicfingers/XIVLauncher.Core)'s releases,
which build XLM and XIVLauncher.Core for ARM64 until upstream does.

This plugin was written with an AI assistant (Claude). It is not affiliated with goatcorp, Blooym
or Square Enix.

## Build

```sh
npm install
npm run build
```

The plugin is the folder with `plugin.json`, `package.json`, `main.py`, `dist/index.js`, `LICENSE`, `THIRD_PARTY.md`
and this README. Zipped as `XLM Setup/…`, it installs from Decky's developer settings ("Install
plugin from ZIP file").
