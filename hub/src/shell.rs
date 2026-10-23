//! The Windows shell: tray icon, the hub window, and the rules around them.
//! Tray, window and single-instance lock follow nerve (D:\GitHub\nerve\source:
//! tray.rs, panels.rs, main.rs acquire_single_instance).
//!
//!   left-click the tray icon   open or raise the hub window
//!   right-click                Open Hub, each screen, Forge state, Restart, Quit
//!   close the window           hides it to the tray; only Quit exits
//!   --tray                     start hidden (what the login start uses)
//!   --autostart on|off         add or remove the login start, then exit
//!
//! The web server runs on a tokio runtime in a background thread; the window
//! is a webview of that same page, so the screens are the ones in web/.

use std::path::PathBuf;
use std::sync::{Arc, Mutex};

use anyhow::{bail, Context, Result};
use tao::dpi::LogicalSize;
use tao::event::{Event, StartCause, WindowEvent};
use tao::event_loop::{ControlFlow, EventLoopBuilder, EventLoopProxy};
use tao::window::{Window, WindowBuilder};
use tray_icon::menu::{Menu, MenuEvent, MenuItem, PredefinedMenuItem};
use tray_icon::{MouseButton, MouseButtonState, TrayIcon, TrayIconBuilder, TrayIconEvent};
use wry::{WebView, WebViewBuilder};

use crate::forge_client::Forge;
use crate::procs::Procs;
use crate::Hub;

/// The seven screens, as in web/src/screens.js, plus the Canon stub.
const SCREENS: [(&str, &str); 7] = [
    ("deep", "1. Deep Research"),
    ("targeted", "2. Targeted Research"),
    ("acquire", "3. Acquisition"),
    ("search", "4. Search Engine"),
    ("youtube", "5. YouTube"),
    ("api", "6. API Layer"),
    ("writer", "7. The Writer"),
];

const RUN_KEY: &str = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run";
const RUN_VALUE: &str = "DeepResearchHub";

#[derive(Debug, Clone)]
enum AppEvent {
    /// Raise the window, on a screen if named.
    Show(Option<String>),
    ServerReady,
    ServerFailed(String),
    /// Forge up (Some(true)), down (Some(false)), or not yet checked.
    Forge(Option<bool>),
    Restart,
    Quit,
}

pub fn run(args: &[String], root: PathBuf, port: u16, procs: Arc<Procs>, forge: Arc<Forge>) -> Result<()> {
    if let Some(i) = args.iter().position(|a| a == "--autostart") {
        return autostart(args.get(i + 1).map(String::as_str));
    }
    let start_hidden = args.iter().any(|a| a == "--tray");
    let waited = args.iter().any(|a| a == "--wait");

    // Exactly one hub. A second launch raises the first, then exits.
    let _instance_lock = match acquire_single_instance(waited) {
        Some(handle) => handle,
        None => {
            let rt = tokio::runtime::Runtime::new()?;
            let _ = rt.block_on(crate::http1::request(
                "127.0.0.1", port, "POST", "/api/shell/show", None, &[], std::time::Duration::from_secs(3),
            ));
            return Ok(());
        }
    };
    // Every app the hub starts is in this job, so none outlives the hub,
    // even when the hub is killed rather than quit.
    let _job = kill_children_with_me();

    let event_loop = EventLoopBuilder::<AppEvent>::with_user_event().build();
    let proxy = event_loop.create_proxy();

    let rt = tokio::runtime::Runtime::new()?;
    let handle = rt.handle().clone();
    let show_proxy = Mutex::new(proxy.clone());
    let hub = Hub {
        root,
        procs: procs.clone(),
        forge: forge.clone(),
        show: Arc::new(move |screen| {
            let _ = show_proxy.lock().unwrap().send_event(AppEvent::Show(screen));
        }),
    };
    let server_proxy = proxy.clone();
    let forge_proxy = proxy.clone();
    std::thread::spawn(move || {
        rt.block_on(async move {
            tokio::spawn(async move {
                let mut rx = forge.subscribe();
                let _ = forge_proxy.send_event(AppEvent::Forge(rx.borrow().up));
                while rx.changed().await.is_ok() {
                    let up = rx.borrow().up;
                    let _ = forge_proxy.send_event(AppEvent::Forge(up));
                }
            });
            let ready = server_proxy.clone();
            if let Err(e) = crate::serve(hub, port, move || {
                let _ = ready.send_event(AppEvent::ServerReady);
            })
            .await
            {
                eprintln!("[hub] server stopped: {e:#}");
                let _ = server_proxy.send_event(AppEvent::ServerFailed(format!("{e:#}")));
            }
        });
    });

    // tray-icon wants the event loop running before the icon is made (nerve:
    // Shell_NotifyIconW can return E_FAIL otherwise), so both wait for Init.
    let mut tray: Option<Tray> = None;
    let mut window: Option<Window> = None;
    let mut webview: Option<WebView> = None;
    let mut pending_show: Option<Option<String>> = if start_hidden { None } else { Some(None) };
    let url = format!("http://127.0.0.1:{port}/");

    event_loop.run(move |event, target, control_flow| {
        *control_flow = ControlFlow::Wait;
        match event {
            Event::NewEvents(StartCause::Init) => match Tray::new(&proxy) {
                Ok(t) => tray = Some(t),
                Err(e) => eprintln!("[hub] no tray icon: {e:#}. The window still works; close it to quit."),
            },

            Event::UserEvent(AppEvent::ServerReady) => {
                let built = WindowBuilder::new()
                    .with_title("Deep Research Hub")
                    .with_inner_size(LogicalSize::new(1280.0, 820.0))
                    .with_visible(false)
                    .build(target)
                    .context("window")
                    .and_then(|w| {
                        let wv = WebViewBuilder::new().with_url(&url).build(&w).context("webview")?;
                        Ok((w, wv))
                    });
                match built {
                    Ok((w, wv)) => {
                        window = Some(w);
                        webview = Some(wv);
                        if let Some(screen) = pending_show.take() {
                            show(window.as_ref(), webview.as_ref(), screen);
                        }
                    }
                    Err(e) => eprintln!("[hub] {e:#}"),
                }
            }

            Event::UserEvent(AppEvent::ServerFailed(msg)) => {
                if let Some(t) = &tray {
                    t.server_failed(&msg);
                }
            }

            Event::UserEvent(AppEvent::Show(screen)) => {
                if window.is_some() {
                    show(window.as_ref(), webview.as_ref(), screen);
                } else {
                    pending_show = Some(screen);
                }
            }

            Event::UserEvent(AppEvent::Forge(up)) => {
                if let Some(t) = &tray {
                    t.forge(up);
                }
            }

            Event::UserEvent(AppEvent::Restart) => {
                handle.block_on(procs.stop_all());
                let hidden = window.as_ref().map(|w| !w.is_visible()).unwrap_or(start_hidden);
                if let Err(e) = relaunch(hidden) {
                    eprintln!("[hub] restart failed, staying up: {e:#}");
                    return;
                }
                tray.take();
                *control_flow = ControlFlow::Exit;
            }

            Event::UserEvent(AppEvent::Quit) => {
                handle.block_on(procs.stop_all());
                tray.take();
                *control_flow = ControlFlow::Exit;
            }

            Event::WindowEvent { event: WindowEvent::CloseRequested, .. } => {
                if tray.is_some() {
                    if let Some(w) = &window {
                        w.set_visible(false);
                    }
                } else {
                    // No tray to come back from: closing is quitting.
                    let _ = proxy.send_event(AppEvent::Quit);
                }
            }

            _ => {}
        }
    });
}

fn show(window: Option<&Window>, webview: Option<&WebView>, screen: Option<String>) {
    let Some(w) = window else { return };
    w.set_visible(true);
    w.set_minimized(false);
    w.set_focus();
    if let (Some(wv), Some(id)) = (webview, screen) {
        // Ids come from the menu or a local caller; keep them plain anyway.
        if !id.is_empty() && id.chars().all(|c| c.is_ascii_alphanumeric()) {
            let _ = wv.evaluate_script(&format!("location.hash = '#/{id}'"));
        }
    }
}

struct Tray {
    icon: TrayIcon,
    forge_item: MenuItem,
}

impl Tray {
    fn new(proxy: &EventLoopProxy<AppEvent>) -> Result<Self> {
        let menu = Menu::new();
        let open = MenuItem::new("Open Hub", true, None);
        menu.append(&open)?;
        menu.append(&PredefinedMenuItem::separator())?;
        let mut screen_items = vec![];
        for (id, label) in SCREENS {
            let item = MenuItem::new(label, true, None);
            menu.append(&item)?;
            screen_items.push((item.id().clone(), id.to_string()));
        }
        menu.append(&MenuItem::new("8. Canon (coming soon)", false, None))?;
        menu.append(&PredefinedMenuItem::separator())?;
        let forge_item = MenuItem::new("Forge: checking…", false, None);
        menu.append(&forge_item)?;
        menu.append(&PredefinedMenuItem::separator())?;
        let restart = MenuItem::new("Restart", true, None);
        let quit = MenuItem::new("Quit", true, None);
        menu.append(&restart)?;
        menu.append(&quit)?;

        let (open_id, restart_id, quit_id) = (open.id().clone(), restart.id().clone(), quit.id().clone());
        let menu_proxy = proxy.clone();
        std::thread::spawn(move || loop {
            if let Ok(event) = MenuEvent::receiver().recv() {
                let ev = if event.id == open_id {
                    AppEvent::Show(None)
                } else if event.id == restart_id {
                    AppEvent::Restart
                } else if event.id == quit_id {
                    AppEvent::Quit
                } else if let Some((_, screen)) = screen_items.iter().find(|(id, _)| *id == event.id) {
                    AppEvent::Show(Some(screen.clone()))
                } else {
                    continue;
                };
                let _ = menu_proxy.send_event(ev);
            }
        });

        let click_proxy = proxy.clone();
        std::thread::spawn(move || loop {
            if let Ok(TrayIconEvent::Click { button: MouseButton::Left, button_state: MouseButtonState::Up, .. }) =
                TrayIconEvent::receiver().recv()
            {
                let _ = click_proxy.send_event(AppEvent::Show(None));
            }
        });

        let icon = TrayIconBuilder::new()
            .with_menu(Box::new(menu))
            .with_menu_on_left_click(false)
            .with_tooltip("Deep Research Hub — Forge: checking…")
            .with_icon(make_icon(false))
            .build()?;
        Ok(Self { icon, forge_item })
    }

    fn forge(&self, up: Option<bool>) {
        let text = match up {
            None => "Forge: checking…",
            Some(true) => "Forge: up",
            Some(false) => "Forge: DOWN — AI actions will fail",
        };
        self.forge_item.set_text(text);
        let _ = self.icon.set_tooltip(Some(format!("Deep Research Hub — {text}")));
        let _ = self.icon.set_icon(Some(make_icon(up == Some(false))));
    }

    fn server_failed(&self, msg: &str) {
        let _ = self.icon.set_tooltip(Some(format!("Deep Research Hub — server failed: {msg}")));
    }
}

/// 16x16 RGBA, drawn like nerve's: an amber "D" on black, with a red corner
/// badge while Forge is down.
fn make_icon(forge_down: bool) -> tray_icon::Icon {
    let size = 16u32;
    let mut rgba = vec![0u8; (size * size * 4) as usize];
    for y in 0..size {
        for x in 0..size {
            let idx = ((y * size + x) * 4) as usize;
            let (r, g, b) = if forge_down && x >= 10 && y >= 10 {
                (0xe5, 0x53, 0x4b)
            } else if in_d(x, y) {
                (0xe8, 0xb3, 0x39)
            } else {
                (0x00, 0x00, 0x00)
            };
            rgba[idx..idx + 4].copy_from_slice(&[r, g, b, 0xff]);
        }
    }
    tray_icon::Icon::from_rgba(rgba, size, size).expect("tray icon pixels")
}

fn in_d(x: u32, y: u32) -> bool {
    let rows = 2..=13;
    let stem = (3..=4).contains(&x) && rows.contains(&y);
    let top_bottom = (3..=9).contains(&x) && (y == 2 || y == 3 || y == 12 || y == 13);
    let bow = (10..=11).contains(&x) && (4..=11).contains(&y);
    stem || top_bottom || bow
}

/// Claim the single-instance lock, or return None if another hub holds it.
/// Session-local mutex, as in nerve; Windows releases it when the process
/// exits, crash included. `wait` (set by Restart) gives the old hub a few
/// seconds to exit first.
fn acquire_single_instance(wait: bool) -> Option<windows::Win32::Foundation::HANDLE> {
    use windows::core::w;
    use windows::Win32::Foundation::{CloseHandle, GetLastError, ERROR_ALREADY_EXISTS};
    use windows::Win32::System::Threading::CreateMutexW;

    for _ in 0..if wait { 40 } else { 1 } {
        unsafe {
            let handle = CreateMutexW(None, true, w!("DeepResearchHubSingleInstance")).ok()?;
            if GetLastError() != ERROR_ALREADY_EXISTS {
                return Some(handle);
            }
            // Our handle keeps the mutex alive; let go before trying again.
            let _ = CloseHandle(handle);
        }
        if wait {
            std::thread::sleep(std::time::Duration::from_millis(250));
        }
    }
    None
}

/// Puts the hub in a job object that kills everything in it when the hub's
/// last handle closes, i.e. when the hub exits for any reason. Children
/// (and their children) join the job on spawn. Breakaway is allowed so
/// Restart can start the next hub outside it.
fn kill_children_with_me() -> Option<windows::Win32::Foundation::HANDLE> {
    use windows::Win32::System::JobObjects::{
        AssignProcessToJobObject, CreateJobObjectW, JobObjectExtendedLimitInformation, SetInformationJobObject,
        JOBOBJECT_EXTENDED_LIMIT_INFORMATION, JOB_OBJECT_LIMIT_BREAKAWAY_OK, JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
    };
    use windows::Win32::System::Threading::GetCurrentProcess;

    unsafe {
        let job = CreateJobObjectW(None, None).ok()?;
        let mut info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION::default();
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | JOB_OBJECT_LIMIT_BREAKAWAY_OK;
        SetInformationJobObject(
            job,
            JobObjectExtendedLimitInformation,
            &info as *const _ as *const std::ffi::c_void,
            std::mem::size_of::<JOBOBJECT_EXTENDED_LIMIT_INFORMATION>() as u32,
        )
        .ok()?;
        if let Err(e) = AssignProcessToJobObject(job, GetCurrentProcess()) {
            eprintln!("[hub] could not join job object ({e}); apps may outlive a crashed hub");
            return None;
        }
        Some(job)
    }
}

/// Starts the next hub outside our job, then this one exits.
fn relaunch(hidden: bool) -> Result<()> {
    use std::os::windows::process::CommandExt;
    const CREATE_BREAKAWAY_FROM_JOB: u32 = 0x0100_0000;

    let exe = std::env::current_exe()?;
    let mut cmd = std::process::Command::new(exe);
    cmd.arg("--wait").creation_flags(CREATE_BREAKAWAY_FROM_JOB);
    if hidden {
        cmd.arg("--tray");
    }
    cmd.spawn().context("start the new hub")?;
    Ok(())
}

/// --autostart on|off: the login start is a value under the per-user Run
/// key, so nothing needs admin rights.
fn autostart(mode: Option<&str>) -> Result<()> {
    let mut cmd = std::process::Command::new("reg");
    match mode {
        Some("on") => {
            let exe = std::env::current_exe()?;
            let value = format!("\"{}\" --tray", exe.display());
            cmd.args(["add", RUN_KEY, "/v", RUN_VALUE, "/t", "REG_SZ", "/d", &value, "/f"]);
        }
        Some("off") => {
            cmd.args(["delete", RUN_KEY, "/v", RUN_VALUE, "/f"]);
        }
        _ => bail!("use --autostart on or --autostart off"),
    }
    let status = cmd.status().context("run reg.exe")?;
    if !status.success() {
        bail!("reg.exe failed ({status})");
    }
    println!("[hub] login start {}", if mode == Some("on") { "on" } else { "off" });
    Ok(())
}
