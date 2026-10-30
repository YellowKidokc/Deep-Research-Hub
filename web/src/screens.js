// The seven screens, in walk-through order. `build` is the milestone that fills it in.
export const SCREENS = [
  { id: "deep", n: 1, name: "Deep Research", build: 7, tabs: ["Queue", "Runs"] },
  { id: "targeted", n: 2, name: "Targeted Research", build: 6, tabs: ["Battery", "Facts"] },
  { id: "acquire", n: 3, name: "Acquisition", build: 3, tabs: ["Scrape", "Links", "Crawl", "Search"] },
  { id: "search", n: 4, name: "Search Engine", build: 4, tabs: ["Query", "Index status", "What's in here"] },
  { id: "youtube", n: 5, name: "YouTube", build: 2, tabs: ["Intake", "Library"] },
  { id: "corpus", n: 6, name: "Corpus Search", build: 2, tabs: ["Search"] },
  { id: "api", n: 7, name: "API Layer", build: 5, tabs: ["Bench", "Slot sets", "Cost log"] },
  { id: "writer", n: 8, name: "The Writer", build: 8, tabs: ["Canon", "Tempo", "Lock", "Output"] },
  { id: "studio", n: 9, name: "Content Studio", build: 9, tabs: ["Launch"] },
];
