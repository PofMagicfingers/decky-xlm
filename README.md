# XLM Setup

A [Decky Loader](https://github.com/SteamDeckHomebrew/decky-loader) plugin that sets up
[XIVLauncher](https://github.com/goatcorp/XIVLauncher.Core) for FINAL FANTASY XIV through
[XLM](https://github.com/Blooym/xlm), from Steam's game mode:

1. Finds the full game (39210) or the free trial (312060) in the Steam libraries, and offers to
   install one when neither is there.
2. Installs its own copy of XLM as the "XLM Decky" compatibility tool (`compatibilitytools.d/XLM-Decky`,
   internal name `xlm-decky`), keeping its `prelaunch.d` and `postlaunch.d` hooks and the
   XIVLauncher.Core it downloaded across updates. An XLM installed otherwise is left alone.
3. Sets XLM Decky as the game's compatibility tool (after a Steam restart, the first time) and
   launches it.

XLM comes from Blooym/xlm's releases on x86_64 (Steam Deck). On aarch64 (Steam on Android through
[DroidDeck](https://github.com/Droid-Deck/DroidDeck)) it comes from
[PofMagicfingers/XIVLauncher.Core](https://github.com/PofMagicfingers/XIVLauncher.Core)'s releases,
which build XLM and XIVLauncher.Core for ARM64 until upstream does.

This plugin was written with an AI assistant (Claude). It is not affiliated with goatcorp, Blooym
or Square Enix.

## Install and play

1. Install [Decky Loader](https://decky.xyz) (from desktop mode on a Steam Deck; DroidDeck has it
   built in).
2. In Decky's settings, turn on **Developer mode**. In the **Developer** tab, choose **Install
   plugin from URL** and enter
   `https://github.com/PofMagicfingers/decky-xlm/releases/latest/download/xlm-setup.zip`.
3. Open **XLM Setup** from the Quick Access menu (the **…** button).
4. If FINAL FANTASY XIV isn't installed, choose **Install the free trial** or **I own the full
   game**, and let Steam download it.
5. Choose **Install XLM**, then **Restart Steam** the first time.
6. Choose **Use XLM Decky for FINAL FANTASY XIV**, then **Play**. XIVLauncher opens: log in with
   your Square Enix account.

### Free trial or full game

Either Steam entry works. Steam only provides the game files and starts XLM; XIVLauncher then logs
in to your Square Enix account and starts the game, so what you can play is set by that account,
not by the Steam entry. On a free trial account, tick XIVLauncher's free trial option. The free
trial entry is the one to install when you don't own the game on Steam.

## Build

```sh
npm install
npm run build
```

The plugin is the folder with `plugin.json`, `package.json`, `main.py`, `dist/index.js`, `LICENSE`, `THIRD_PARTY.md`
and this README. Zipped as `XLM Setup/…`, it installs from Decky's developer settings ("Install
plugin from ZIP file").
