import {
  ButtonItem,
  Field,
  PanelSection,
  PanelSectionRow,
  staticClasses,
} from "@decky/ui";
import { callable, definePlugin, toaster } from "@decky/api";
import { useEffect, useState } from "react";
import { FaGamepad } from "react-icons/fa";

interface Game {
  appid: number;
  name: string;
  state: "installed" | "installing" | null;
  compatTool: string | null;
}

interface Status {
  arch: string;
  source: string;
  steamRoot: string | null;
  xlmInstalled: boolean;
  restartNeeded: boolean;
  toolName: string;
  games: Game[];
}

const FREE_TRIAL = 312060;
const FULL_GAME = 39210;

const getStatus = callable<[], Status>("status");
const installXlm = callable<[], Status>("install_xlm");

// @decky/ui's SteamClient typings resolve "URL" to the DOM's URL class.
function installGame(appid: number) {
  (SteamClient.URL as unknown as { ExecuteSteamURL(url: string): void }).ExecuteSteamURL(`steam://install/${appid}`);
}

// The tool Steam uses for the app right now; config.vdf only has it once Steam saved it.
function currentTool(game: Game): string | null {
  const details = window.appDetailsStore?.GetAppDetails(game.appid);
  return details?.strCompatToolName || game.compatTool;
}

function Content() {
  const [status, setStatus] = useState<Status | null>(null);
  const [chosen, setChosen] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    try {
      setStatus(await getStatus());
    } catch (e) {
      setError(String(e));
    }
  };

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 5000);
    return () => clearInterval(timer);
  }, []);

  if (error) {
    return (
      <PanelSection>
        <PanelSectionRow>
          <Field label="Error" description={error} />
        </PanelSectionRow>
      </PanelSection>
    );
  }
  if (!status) {
    return (
      <PanelSection>
        <PanelSectionRow>
          <Field label="Checking…" />
        </PanelSectionRow>
      </PanelSection>
    );
  }

  const installed = status.games.filter((g) => g.state === "installed");
  const installing = status.games.filter((g) => g.state === "installing");

  const onInstallXlm = async () => {
    setBusy(true);
    try {
      setStatus(await installXlm());
      toaster.toast({ title: "XLM", body: "Installed" });
      await refresh();
    } catch (e) {
      toaster.toast({ title: "XLM", body: `Install failed: ${e}` });
    } finally {
      setBusy(false);
    }
  };

  const useXlm = (game: Game) => {
    SteamClient.Apps.SpecifyCompatTool(game.appid, status.toolName);
    setChosen({ ...chosen, [game.appid]: status.toolName });
  };

  return (
    <>
      <PanelSection title="Game">
        {installed.length === 0 && installing.length === 0 && (
          <>
            <PanelSectionRow>
              <Field label="FINAL FANTASY XIV is not installed" />
            </PanelSectionRow>
            <PanelSectionRow>
              <ButtonItem layout="below" onClick={() => installGame(FREE_TRIAL)}>
                Install the free trial
              </ButtonItem>
            </PanelSectionRow>
            <PanelSectionRow>
              <ButtonItem layout="below" onClick={() => installGame(FULL_GAME)}>
                I own the full game
              </ButtonItem>
            </PanelSectionRow>
          </>
        )}
        {installing.map((game) => (
          <PanelSectionRow key={game.appid}>
            <Field label={game.name} description="Installing in Steam…" />
          </PanelSectionRow>
        ))}
        {installed.map((game) => (
          <PanelSectionRow key={game.appid}>
            <Field label={game.name} description="Installed" />
          </PanelSectionRow>
        ))}
      </PanelSection>

      <PanelSection title="XLM Decky">
        <PanelSectionRow>
          <Field
            label={status.xlmInstalled ? "Installed" : "Not installed"}
            description={`${status.arch} build, from ${new URL(status.source).pathname.split("/").slice(1, 3).join("/")}`}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem layout="below" disabled={busy || !status.steamRoot} onClick={onInstallXlm}>
            {busy ? "Installing…" : status.xlmInstalled ? "Update XLM" : "Install XLM"}
          </ButtonItem>
        </PanelSectionRow>
        {status.restartNeeded && (
          <PanelSectionRow>
            <Field label="Steam needs a restart to see XLM Decky" />
            <ButtonItem layout="below" onClick={() => SteamClient.User.StartRestart(false)}>
              Restart Steam
            </ButtonItem>
          </PanelSectionRow>
        )}
      </PanelSection>

      {status.xlmInstalled && !status.restartNeeded && installed.length > 0 && (
        <PanelSection title="Launch">
          {installed.map((game) => {
            const tool = chosen[game.appid] ?? currentTool(game);
            return (
              <PanelSectionRow key={game.appid}>
                {tool === status.toolName ? (
                  <ButtonItem layout="below" onClick={() => SteamClient.Apps.RunGame(String(game.appid), "", -1, 100)}>
                    Play {game.name}
                  </ButtonItem>
                ) : (
                  <ButtonItem layout="below" onClick={() => useXlm(game)}>
                    Use XLM Decky for {game.name}
                  </ButtonItem>
                )}
              </PanelSectionRow>
            );
          })}
        </PanelSection>
      )}
    </>
  );
}

export default definePlugin(() => ({
  name: "XLM Setup",
  titleView: <div className={staticClasses.Title}>XLM Setup</div>,
  content: <Content />,
  icon: <FaGamepad />,
}));
