//! One module per screen. Each is a thin shell: it reads that screen's output
//! folder under data\ and hands it to the page. Starting the screen's app goes
//! through hub\launch.json like everything else.

pub mod deep_research;
pub mod youtube;
