import { useEffect, useState } from "react";
import { SCREENS, runningFor } from "./screens.js";
import { api } from "./api.js";
import { Icon } from "./Icons.jsx";
import Home from "./screens/Home.jsx";
import Placeholder from "./screens/Placeholder.jsx";
import YouTube from "./screens/youtube/index.jsx";
import DeepResearch from "./screens/deep/index.jsx";
import Acquisition from "./screens/acquire/index.jsx";

const BUILT = { deep: DeepResearch, acquire: Acquisition, youtube: YouTube };

// Route lives in the URL hash (#/youtube/Intake) so a reload lands in the same place.
function readHash() {
  const [screen = "", tab = ""] = decodeURIComponent(location.hash.replace(/^#\/?/, "")).split("/");
  return { screen, tab };
}

export default function App() {
  const [route, setRoute] = useState(readHash());
  useEffect(() => {
    const on = () => setRoute(readHash());
    addEventListener("hashchange", on);
    return () => removeEventListener("hashchange", on);
  }, []);

  // Hub state the rail and header show: jobs per screen, and Forge.
  const [procs, setProcs] = useState([]);
  const [forgeState, setForge] = useState(null);
  useEffect(() => {
    const poll = () => {
      api("/procs").then(setProcs).catch(() => {});
      api("/shell/state").then((s) => setForge(s.forge)).catch(() => setForge(null));
    };
    poll();
    const t = setInterval(poll, 3000);
    return () => clearInterval(t);
  }, []);

  // Clicking the open screen's icon again relaunches it (fresh mount).
  const [mount, setMount] = useState(0);
  const relaunch = (s) => { if (s.id === route.screen) setMount((m) => m + 1); };

  const screen = SCREENS.find((s) => s.id === route.screen);
  const tab = screen && screen.tabs.includes(route.tab) ? route.tab : screen?.tabs[0];
  const Built = screen && BUILT[screen.id];

  return (
    <div className="shell">
      <nav className="rail">
        {SCREENS.map((s) => {
          const on = runningFor(s, procs);
          const state = s.stub ? "coming soon" : on ? "running" : "stopped";
          return (
            <a key={s.id} href={`#/${s.id}`} title={`${s.n}. ${s.name} — ${state}`} onClick={() => relaunch(s)}
               className={[s.id === route.screen && "active", s.stub && "stub"].filter(Boolean).join(" ")}>
              <Icon id={s.id} />
              {!s.stub && <span className={on ? "run on" : "run"} />}
            </a>
          );
        })}
      </nav>
      <div className="main">
        <header className="top">
          <a href="#/" className={screen ? "" : "active"}>Home</a>
          {screen && <span className="crumb">{screen.n}. {screen.name}</span>}
          {screen && (
            <span className="tabs">
              {screen.tabs.map((t) => (
                <a key={t} href={`#/${screen.id}/${t}`} className={t === tab ? "active" : ""}>{t}</a>
              ))}
            </span>
          )}
          <span className={forgeState?.up === false ? "forge down" : "forge"} title={forgeState?.error || forgeState?.url || ""}>
            {forgeState == null ? "Forge: ?" : forgeState.up == null ? "Forge: checking" : forgeState.up ? "Forge: up" : "Forge: DOWN"}
          </span>
        </header>
        <section className="body">
          {!screen ? <Home /> : Built ? <Built key={mount} tab={tab} /> : <Placeholder screen={screen} tab={tab} />}
        </section>
      </div>
    </div>
  );
}
