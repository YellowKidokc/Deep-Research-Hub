import { useEffect, useState } from "react";
import { SCREENS } from "./screens.js";
import { Icon } from "./Icons.jsx";
import Home from "./screens/Home.jsx";
import Placeholder from "./screens/Placeholder.jsx";
import YouTube from "./screens/youtube/index.jsx";
import DeepResearch from "./screens/deep/index.jsx";

const BUILT = { deep: DeepResearch, youtube: YouTube };

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

  const screen = SCREENS.find((s) => s.id === route.screen);
  const tab = screen && screen.tabs.includes(route.tab) ? route.tab : screen?.tabs[0];
  const Built = screen && BUILT[screen.id];

  return (
    <div className="shell">
      <nav className="rail">
        {SCREENS.map((s) => (
          <a key={s.id} href={`#/${s.id}`} title={`${s.n}. ${s.name}`}
             className={s.id === route.screen ? "active" : ""}>
            <Icon id={s.id} />
          </a>
        ))}
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
        </header>
        <section className="body">
          {!screen ? <Home /> : Built ? <Built tab={tab} /> : <Placeholder screen={screen} tab={tab} />}
        </section>
      </div>
    </div>
  );
}
