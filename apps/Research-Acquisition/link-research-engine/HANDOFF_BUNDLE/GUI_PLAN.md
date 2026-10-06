# GUI Plan

## Purpose

Turn the updated intake workbook into the first real desktop interface plan for the Link Research Engine.

This GUI should preserve:

- dropdown-driven speed
- note-driven nuance
- optional media/API expansion
- workbook-quality structure

It should use the existing dark/blue desktop style already proven in the Truth Engine shell.

## Canonical Inputs Used

- `C:\Users\lowes\Desktop\TEMPLATE_THEOPHYSICS_FACTS.xlsx`
- `RESEARCH_INTAKE` sheet
- current Link Research Engine repo structure
- existing Truth Engine style reference (dark + blue + gold accent shell)

## Structured Output

### Primary shell

Recommended framework:
- `PySide6`

Recommended shell sections:
- top status/header bar
- left navigation or top nav tabs
- central intake panel
- lower results/log/output panel

### Recommended tabs

1. `INTAKE`
2. `DISCOVERY`
3. `LINKS`
4. `RIPPER`
5. `RESEARCH`
6. `WORKBOOK`
7. `WORKSPACE`
8. `MEDIA` (shown only when activated)
9. `API` (shown only when activated)

## Intake Screen Spec

### Section A — Run Metadata

This stays at the top and travels with the run.

Fields:
- `Run Name`
- `Category`
- `Trust Mode`
- `Author / Owner`
- `Topics`
- `Tags`
- `Purpose`
- `Notes`

UI pattern:
- dropdowns for strongly typed values
- short text inputs for metadata
- one multi-line note area

### Section B — Core Intake (Q1–Q6)

These are the universal intake controls.

Each question gets:
- label
- dropdown
- short helper text
- note field directly underneath

#### Q1
**What is the target type?**

Dropdown examples:
- `single_case`
- `category`
- `person`
- `organization`
- `topic`
- `keyword_cluster`
- `link_list`
- `domain`

Note field use:
- aliases
- scope clarification
- case boundaries

#### Q2
**What is the research intent?**

Dropdown examples:
- `define_it`
- `aggregate_sources`
- `rip_site`
- `find_outgoing_links`
- `find_best_evidence`
- `build_timeline`
- `build_entity_map`

Note field use:
- keyword hints
- what matters most
- what success looks like

#### Q3
**What source scope?**

Dropdown examples:
- `wikipedia_only`
- `trusted_hubs`
- `web_wide`
- `domain_specific`
- `archives_gov_legal`
- `mixed`

Note field use:
- include/exclude domains
- trusted exceptions
- domains to avoid

#### Q4
**What depth?**

Dropdown examples:
- `top_10`
- `top_25`
- `top_50`
- `one_hop`
- `two_hops`
- `deep_crawl`

Note field use:
- hard limits
- priority rip targets
- cost discipline

#### Q5
**What output do you want?**

Dropdown examples:
- `link_list`
- `source_inventory`
- `ripped_pages`
- `entities`
- `timeline_events`
- `workbook`
- `notebook`
- `package_json`

Note field use:
- consumer of output
- what fields must be included
- whether output is human-facing or machine-facing

#### Q6
**How should it organize results?**

Dropdown examples:
- `by_case`
- `by_source_type`
- `by_date`
- `by_entity`
- `by_confidence`
- `by_domain`

Note field use:
- audience preference
- grouping nuance
- sorting priority

### Section C — Optional Media / API Intake (Q7–Q9)

Collapsed by default.
Only expands when media/API mode is enabled.

#### Q7
**Include media / video sources?**

Dropdown / toggle:
- `no`
- `yes_youtube`
- `yes_mixed_media`

Notes:
- channel names
- playlists
- URLs
- exclusions

#### Q8
**What media asset types do you want?**

Dropdown examples:
- `metadata_only`
- `transcripts_only`
- `metadata_and_transcripts`
- `full_research_harvest`
- `comments_plus_transcripts`

Notes:
- comment exclusions
- transcript preference
- timestamp rules

#### Q9
**Media harvest mode?**

Dropdown examples:
- `top_10_videos`
- `top_25_videos`
- `channel_inventory`
- `playlist_only`
- `date_range_limited`
- `deep_media_harvest`

Notes:
- channel exclusions
- date ranges
- max volume

## UX Rules

### Rule 1
Dropdown first, notes second.

The machine should be able to act on the dropdown value alone.
The notes improve precision but should not be the only source of meaning.

### Rule 2
Media/API controls stay hidden unless activated.

The core intake must stay visually calm.

### Rule 3
Large fonts and high readability.

Current style is strong, but body text and input text should be slightly larger than the current Truth Engine screen.

### Rule 4
Status should always be visible.

Include a slim run-status bar showing:
- current mode
- links found
- links kept
- ripped pages
- current stage

### Rule 5
Workbook quality remains the standard.

The GUI is not replacing workbook quality.
It should produce workbook outputs that feel as deliberate and clean as the current Excel deliverables.

## First GUI Build Order

1. Build `INTAKE` tab only
2. Wire Q1–Q6 fields to a saved config object
3. Add optional Q7–Q9 expandable media section
4. Add `RUN` action
5. Show output/log panel
6. Add workbook export button

## What This Screen Must Do

- read structured intake
- capture notes cleanly
- save run config
- trigger the selected pipeline
- display progress
- open output workbook

## Audit Footer

### Where We Are Right

The updated workbook now provides a strong GUI blueprint: typed dropdowns, note rows, and optional media/API expansion.

### Where We Might Be Wrong

Some advanced metadata may need to move to a secondary panel if the intake screen becomes crowded.

### What We Think

This is the right next interface layer. The intake workbook should now be treated as the GUI specification for the PySide6 shell.
