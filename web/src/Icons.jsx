// One plain stroke glyph per screen. 20x20, currentColor.
const P = {
  // a fork: one line splitting into two
  deep: <path d="M10 18V10M10 10L4 3M10 10l6-7" />,
  // crosshair
  targeted: <><circle cx="10" cy="10" r="6" /><path d="M10 1v5M10 14v5M1 10h5M14 10h5" /></>,
  // arrow coming home into a tray
  acquire: <path d="M10 2v11M5 8l5 5 5-5M3 17h14" />,
  // magnifier
  search: <><circle cx="8" cy="8" r="5.5" /><path d="M12 12l6 6" /></>,
  // play in a frame
  youtube: <><rect x="2" y="4" width="16" height="12" /><path d="M8 7.5v5l4.5-2.5z" /></>,
  // braces
  api: <path d="M7 3H6a2 2 0 0 0-2 2v3l-2 2 2 2v3a2 2 0 0 0 2 2h1M13 3h1a2 2 0 0 1 2 2v3l2 2-2 2v3a2 2 0 0 1-2 2h-1" />,
  // pen nib on a line
  writer: <path d="M3 17l2-6L14 2l4 4-9 9-6 2zM12 4l4 4M2 19h16" />,
  // open book
  canon: <path d="M10 5v12M10 5C8 3.5 5 3 2 3.5v12c3-.5 6 0 8 1.5 2-1.5 5-2 8-1.5v-12C15 3 12 3.5 10 5z" />,
};

export function Icon({ id }) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor"
         strokeWidth="1.5" strokeLinecap="square" aria-hidden="true">
      {P[id]}
    </svg>
  );
}
