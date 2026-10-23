// The seven screens, in walk-through order. `build` is the milestone that fills it in.
// `launches`: hub/launch.json ids whose jobs belong to the screen (rail shows running/stopped).
// `stub`: an icon slot only; opens a "coming soon" page.
export const SCREENS = [
  { id: "deep", n: 1, name: "Deep Research", build: 7, tabs: ["Queue", "Runs"], launches: ["deep.", "gptr."] },
  { id: "targeted", n: 2, name: "Targeted Research", build: 6, tabs: ["Battery", "Facts"], launches: [] },
  { id: "acquire", n: 3, name: "Acquisition", build: 3, tabs: ["Scrape", "Links", "Crawl", "Search"],
    launches: ["acquire.", "search.marginalia", "deepcrawl."] },
  { id: "search", n: 4, name: "Search Engine", build: 4, tabs: ["Query", "Index status", "What's in here"], launches: [] },
  { id: "youtube", n: 5, name: "YouTube", build: 2, tabs: ["Intake", "Library"], launches: ["youtube."] },
  { id: "api", n: 6, name: "API Layer", build: 5, tabs: ["Bench", "Slot sets", "Cost log"], launches: [] },
  { id: "writer", n: 7, name: "The Writer", build: 8, tabs: ["Canon", "Tempo", "Lock", "Output"], launches: ["openwriter."] },
  { id: "canon", n: 8, name: "Canon", stub: true, tabs: ["Browse"], launches: [] },
];

export const runningFor = (screen, procs) =>
  procs.some((p) => p.status === "running" && screen.launches.some((l) => p.launch_id.startsWith(l)));
