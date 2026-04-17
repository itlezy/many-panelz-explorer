# many-panelz-explorer — Comprehensive Backlog

This document is the canonical backlog for `many-panelz-explorer`.
It consolidates the older roadmap files, the shortcut backlog, and the recent
CommanderStyle research into one product-facing view.
Older root-level planning notes (`ROADMAP.md`, `ROADMAPEXT.md`, `REFAC.md`, and
`MMPERFOBS.md`) are retained only as archived historical references and are not
authoritative backlog sources.
The goal is not to reproduce another file manager. The goal is to build a
dense, keyboard-capable, many-panel explorer that borrows proven ideas where
they strengthen the app's own identity.
The product lens is always:

- many panelz first
- CommanderStyle as inspiration, not cloning
- dense operational UI over explanatory UI
- no embedded command line

## Table of Contents

- [Summary Table](#summary-table)
- [Status Meanings](#status-meanings)
- [Phase 1](#phase-1)
- [Phase 2](#phase-2)
- [Phase 3](#phase-3)
- [Rejected Principles And Features](#rejected-principles-and-features)

## Summary Table

| ID | Title | Phase | Theme | Status |
|---|---|---:|---|---|
| `ITEM_001` | Bookmarks and Hotlist Baseline | 1 | navigation | `DONE` |
| `ITEM_002` | Folder Size Calculation Baseline | 1 | file operations | `DONE` |
| `ITEM_003` | Storage Overview Status Row | 1 | status visibility | `DONE` |
| `ITEM_004` | Dynamic Context Menu Baseline | 1 | contextual workflows | `DONE` |
| `ITEM_005` | Separate Hidden vs System Visibility | 1 | file display | `DONE` |
| `ITEM_006` | Cursor vs Marked Items Model | 1 | selection semantics | `DONE` |
| `ITEM_007` | Right-Button Selection Mode Foundation | 1 | mouse interaction | `DONE` |
| `ITEM_008` | Root Controls with Drive-Like Semantics | 1 | root navigation | `DONE` |
| `ITEM_009` | Breadcrumb, History, and Bookmarks Toolbar Access | 1 | navigation chrome | `DONE` |
| `ITEM_010` | Drive-Root Parent Row Behavior | 1 | file display | `DONE` |
| `ITEM_011` | Directory Display Formatting Options | 1 | file display | `DONE` |
| `ITEM_012` | CommanderStyle Name Sorting Methods | 1 | sorting | `DONE` |
| `ITEM_013` | File and Root Icon Pipeline | 1 | visual scanning | `DONE` |
| `ITEM_014` | CommanderStyle Keyboard and Target-Pane Baseline | 1 | interaction model | `DONE` |
| `ITEM_015` | Function Key Bar Adapted to Many Panels | 1 | operational chrome | `PLANNED` |
| `ITEM_016` | Rich Per-Panel Footer and Status Strip | 1 | status visibility | `PARTIAL` |
| `ITEM_017` | Numeric Keypad Marking Suite | 1 | selection operations | `DONE` |
| `ITEM_018` | Dense Panel Chrome Mode | 1 | UI density | `PLANNED` |
| `ITEM_019` | Multi-Panel Source and Target Affordance Upgrade | 1 | many-panel identity | `PARTIAL` |
| `ITEM_020` | Hotlist Expansion for Many Panels | 1 | bookmarks | `PLANNED` |
| `ITEM_021` | Quick Filter Surface Without Command Line | 1 | filtering | `PARTIAL` |
| `ITEM_022` | Keyboard Discoverability Layer | 1 | usability | `PLANNED` |
| `ITEM_023` | Pane Sync and Mirror Navigation | 1 | multi-panel workflows | `PLANNED` |
| `ITEM_024` | Open in many-panelz and Open in Explorer Workflow | 1 | context actions | `PARTIAL` |
| `ITEM_048` | Visible Git Branch and Dirty Surface | 1 | contextual workflows | `PARTIAL` |
| `ITEM_025` | Tab Context Menu and Advanced Tab Workflow | 2 | tabs | `PARTIAL` |
| `ITEM_026` | Column Control, Density, and Lightweight View Presets | 2 | file list presentation | `PARTIAL` |
| `ITEM_027` | Per-Folder View Memory | 2 | persistence | `PLANNED` |
| `ITEM_028` | Compare, Branch, and Structured Selection Workflows | 2 | power workflows | `PLANNED` |
| `ITEM_029` | Footer Aggregates Beyond Size | 2 | status visibility | `PARTIAL` |
| `ITEM_030` | Named Workspace and Tab Sessions | 2 | workspace state | `PARTIAL` |
| `ITEM_047` | First-Run Workspace Onboarding and Tool Detection | 2 | onboarding | `PLANNED` |
| `ITEM_031` | Visual Role Cues for Active, Target, and Related Panels | 2 | many-panel identity | `PARTIAL` |
| `ITEM_032` | Saved Filters and Search Workflows | 2 | filtering | `PLANNED` |
| `ITEM_033` | Export and Import Full App Configuration | 2 | portability | `PLANNED` |
| `ITEM_034` | Repo-Aware Overlays and Signals | 2 | contextual workflows | `PARTIAL` |
| `ITEM_035` | Checkbox-Assisted Marking Column | 2 | accessibility | `PLANNED` |
| `ITEM_036` | Recent Files and Virtual Collection Views | 2 | alternate navigation | `PLANNED` |
| `ITEM_037` | Thumbnail and Media-Oriented Alternate Views | 3 | alternate views | `PLANNED` |
| `ITEM_038` | Metadata Columns and Rich File Attributes | 3 | file list presentation | `PLANNED` |
| `ITEM_039` | Advanced Tree or Alternate Navigation Surfaces | 3 | navigation | `PLANNED` |
| `ITEM_040` | Saved Search Bookmarks and Reusable Virtual Views | 3 | search workflows | `PLANNED` |
| `ITEM_041` | Embedded Command Line | — | shell integration | `REJECTED` |
| `ITEM_042` | Literal CommanderStyle Product Clone | — | product direction | `REJECTED` |
| `ITEM_043` | Two-Panel-Only Assumptions | — | architecture | `REJECTED` |
| `ITEM_044` | Legacy 8.3 Filename Modes | — | legacy compatibility | `REJECTED` |
| `ITEM_045` | Brief or Tree Parity as a Default Goal | — | view modes | `REJECTED` |
| `ITEM_046` | Remote Client Parity as a Core Product Goal | — | scope discipline | `REJECTED` |

## Status Meanings

| Status | Meaning |
|---|---|
| `DONE` | Already implemented or effectively present in the current app surface. |
| `PARTIAL` | A meaningful baseline is already shipped, but the backlog item still has a clear follow-up scope. |
| `PLANNED` | Approved backlog direction for future work. |
| `REJECTED` | Intentionally excluded from the product direction. |

Prefer finishing `PARTIAL` items before starting higher-phase greenfield work unless
there is a strong dependency or a deliberate product reprioritization.

## Phase 1

Phase 1 is about making the app feel like a serious many-panel commander.
The priority is explicit marked-item workflows, dense always-visible operations,
strong root and history navigation, and per-panel status that still scales when
the window contains more than two panels.

### ITEM_001 — Bookmarks and Hotlist Baseline

- Status: `DONE`
- Phase: `1`
- Theme: navigation
- CommanderStyle inspiration: fast bookmark and hotlist access for repeatedly used directories
- many-panelz direction: keep bookmark access fast from any active panel without assuming a fixed left or right side
- Notes:
- The app already has bookmark folders and entries stored outside session state.
- Bookmarks are usable from the menu surface and the panel toolbar path workflow.
- This is the baseline to expand later into stronger many-panel hotlist behaviors.

### ITEM_002 — Folder Size Calculation Baseline

- Status: `DONE`
- Phase: `1`
- Theme: file operations
- CommanderStyle inspiration: on-demand directory size calculation from the file list
- many-panelz direction: keep size calculation panel-local and non-blocking so many lists can stay responsive
- Notes:
- The app already supports on-demand folder size calculation.
- Space and explicit size commands already feed the current details view.
- The next backlog work is about richer footer summaries, not basic calculation.

### ITEM_003 — Storage Overview Status Row

- Status: `DONE`
- Phase: `1`
- Theme: status visibility
- CommanderStyle inspiration: always-visible free-space and drive usage context
- many-panelz direction: keep one global storage row while later adding stronger per-panel status
- Notes:
- The app already shows discovered storage roots in a second status row.
- This supports copy and move decisions without leaving the window.
- Later work should complement it with richer panel-local summaries.

### ITEM_004 — Dynamic Context Menu Baseline

- Status: `DONE`
- Phase: `1`
- Theme: contextual workflows
- CommanderStyle inspiration: task-specific commands surfaced close to the active path
- many-panelz direction: preserve context-sensitive workflows but tie them to the active panel and current path, not a shell console model
- Notes:
- Python, Git, and Node-aware actions already exist.
- This is a strong foundation for later context overlays and richer workspace actions.
- It should remain panel-aware rather than becoming a generic launcher surface.

### ITEM_005 — Separate Hidden vs System Visibility

- Status: `DONE`
- Phase: `1`
- Theme: file display
- CommanderStyle inspiration: independent hidden and system visibility controls
- many-panelz direction: preserve independent visibility in each panel runtime and shared settings
- Notes:
- Hidden and system visibility are already split.
- The behavior already maps cleanly to multi-panel navigation and filtering.
- This should remain a first-class display control, not a combined legacy toggle.

### ITEM_006 — Cursor vs Marked Items Model

- Status: `DONE`
- Phase: `1`
- Theme: selection semantics
- CommanderStyle inspiration: operation targets are marked items, not merely the focused row
- many-panelz direction: keep row focus independent from operation targets across all panels and tabs
- Notes:
- Marked rows now represent the authoritative operation set.
- Cursor movement and mark state are intentionally distinct.
- This is a core product behavior and should not regress into pure Qt row selection.

### ITEM_007 — Right-Button Selection Mode Foundation

- Status: `DONE`
- Phase: `1`
- Theme: mouse interaction
- CommanderStyle inspiration: right-button marking, icon click toggles, and delayed context menu behavior
- many-panelz direction: preserve commander mouse semantics in each file list while keeping multi-panel focus rules clear
- Notes:
- Right-button mode and icon-click marking are already supported.
- Quick right click marks, while hold opens the menu.
- This should be extended, not redesigned, in later selection backlog work.

### ITEM_008 — Root Controls with Drive-Like Semantics

- Status: `DONE`
- Phase: `1`
- Theme: root navigation
- CommanderStyle inspiration: drive buttons, drive list, and root jump behavior
- many-panelz direction: map drive switching to generic root controls that scale to local roots, mount roots, and workspace roots
- Notes:
- Root buttons, root picker, and root combo already exist.
- The current model already supports deeper root matching than simple drive letters.
- This is the app’s many-panel replacement for classic drive bars.

### ITEM_009 — Breadcrumb, History, and Bookmarks Toolbar Access

- Status: `DONE`
- Phase: `1`
- Theme: navigation chrome
- CommanderStyle inspiration: current-dir bar, history popup, and hotlist access
- many-panelz direction: keep these controls visible on every panel toolbar so navigation remains local to the active work surface
- Notes:
- Breadcrumbs, history button, and bookmarks button already exist.
- This keeps navigation close to the current panel instead of only in top menus.
- Later work should make this denser and more discoverable.

### ITEM_010 — Drive-Root Parent Row Behavior

- Status: `DONE`
- Phase: `1`
- Theme: file display
- CommanderStyle inspiration: showing a parent row at drive root that returns to the drive list
- many-panelz direction: the synthetic `..` row should open the app’s root picker rather than inventing a fake filesystem parent
- Notes:
- This behavior is already in place.
- It fits the app’s generic root model better than copying shell namespace behavior.
- It is a good example of adaptation instead of cloning.

### ITEM_011 — Directory Display Formatting Options

- Status: `DONE`
- Phase: `1`
- Theme: file display
- CommanderStyle inspiration: bracketed directories and optional trailing backslash formatting
- many-panelz direction: configurable directory rendering should aid scanning without altering the underlying filesystem model
- Notes:
- Brackets and trailing backslash are already configurable.
- The feature is purely presentational and low-risk.
- It supports high-density scanning in details view.

### ITEM_012 — CommanderStyle Name Sorting Methods

- Status: `DONE`
- Phase: `1`
- Theme: sorting
- CommanderStyle inspiration: locale, codepoint, and natural sorting choices
- many-panelz direction: richer sorting should strengthen dense file-list usage while staying compatible with the app’s own directory sort rules
- Notes:
- Multiple name sort methods are already supported.
- Directory sort mode remains separately configurable.
- This provides a solid foundation for later per-folder view memory.

### ITEM_013 — File and Root Icon Pipeline

- Status: `DONE`
- Phase: `1`
- Theme: visual scanning
- CommanderStyle inspiration: icon-rich file managers that support fast visual recognition
- many-panelz direction: icons should remain compact scanning aids in the file list and root controls, not decorative chrome
- Notes:
- File icons and root icons are already supported.
- Hidden-item dimming is already integrated into the same pipeline.
- This should remain optional and density-conscious.

### ITEM_014 — CommanderStyle Keyboard and Target-Pane Baseline

- Status: `DONE`
- Phase: `1`
- Theme: interaction model
- CommanderStyle inspiration: function-key file actions and explicit source-target workflows
- many-panelz direction: keep the current target-pane operations as the baseline, then generalize the cues for more than two panels
- Notes:
- Core file actions, root jumping, tab switching, and target-pane shortcuts already exist.
- This is the current interaction baseline, not the final discoverability layer.
- Later backlog work should clarify and surface these affordances better.

### ITEM_015 — Function Key Bar Adapted to Many Panels

- Status: `PLANNED`
- Phase: `1`
- Theme: operational chrome
- CommanderStyle inspiration: bottom function-key strip with visible commands
- many-panelz direction: show panel-aware actions and source-target meaning without assuming exactly two panes
- Notes:
- The strip should reflect the current active panel context.
- Labels should stay short and operational, not tutorial-like.
- It should coexist with menus and shortcuts rather than replace them.

### ITEM_016 — Rich Per-Panel Footer and Status Strip

- Status: `PARTIAL`
- Phase: `1`
- Theme: status visibility
- CommanderStyle inspiration: always-visible selected counts, totals, and drive context
- many-panelz direction: each panel should own a compact footer that remains legible even when many panels are visible
- Notes:
- The app already ships a per-tab footer with marked/visible counts, file and directory counts, known-size totals, pending folder-size counts, and free-space text.
- The remaining work is to make the footer denser and more role-aware, especially when many panels are visible at once.
- Queue and active-work signals should complement the footer without forcing the queue dock open.

### ITEM_017 — Numeric Keypad Marking Suite

- Status: `DONE`
- Phase: `1`
- Theme: selection operations
- CommanderStyle inspiration: numeric keypad marking, invert, restore, and same-extension actions
- many-panelz direction: extend mark operations without reintroducing ambiguous Qt selection semantics
- Notes:
- `Num +`, `Num -`, `Num *`, and `Num /` now drive bulk mark, unmark, invert, and restore.
- Scope is configurable as files only or files plus directories.
- `Alt+Num +` and `Alt+Num -` now mark or unmark same-extension files from the current row.

### ITEM_018 — Dense Panel Chrome Mode

- Status: `PLANNED`
- Phase: `1`
- Theme: UI density
- CommanderStyle inspiration: compact always-visible toolbars with minimal padding
- many-panelz direction: provide an explicit dense mode that improves information per panel rather than copying another product’s layout literally
- Notes:
- Prioritize toolbar padding, row heights, tab density, and footer density.
- The mode should help when the window shows several simultaneous panels.
- The app should keep its own visual identity while becoming more operationally compact.

### ITEM_019 — Multi-Panel Source and Target Affordance Upgrade

- Status: `PARTIAL`
- Phase: `1`
- Theme: many-panel identity
- CommanderStyle inspiration: strong source-target framing for copy and move workflows
- many-panelz direction: generalize source-target cues for N panels instead of keeping them implicit or locked to a left-right mental model
- Notes:
- The app already has active and target panel tinting plus a real target-panel resolver for copy, move, and open-in-target actions.
- The remaining work is to make role assignment more obvious when more than two panels are visible.
- The follow-up should reduce left-right assumptions in labels and make target selection easier to understand at a glance.

### ITEM_020 — Hotlist Expansion for Many Panels

- Status: `PLANNED`
- Phase: `1`
- Theme: bookmarks
- CommanderStyle inspiration: nested hotlist workflows and quick directory jumps
- many-panelz direction: expand hotlist behavior so entries can open in the current tab, a new tab, or another chosen panel
- Notes:
- The hotlist should remain fast enough for keyboard use.
- Nested folders and favorite groups should stay compact.
- This is a multi-panel navigation tool, not just a static bookmarks file editor.

### ITEM_021 — Quick Filter Surface Without Command Line

- Status: `PARTIAL`
- Phase: `1`
- Theme: filtering
- CommanderStyle inspiration: quick file filtering and show-mode toggles
- many-panelz direction: strengthen inline filtering and file-list modes while explicitly excluding any command-line workflow
- Notes:
- The app already has a panel-local inline filter overlay that opens from typing and pushes text into the active tab filter state.
- The remaining work is to make filter state more visible, reversible, and discoverable without changing the no-command-line direction.
- Keep this item focused on fast inline filtering; reusable saved filters and broader search workflows belong in `ITEM_032`.

### ITEM_022 — Keyboard Discoverability Layer

- Status: `PLANNED`
- Phase: `1`
- Theme: usability
- CommanderStyle inspiration: products that teach their shortcuts through persistent chrome
- many-panelz direction: surface the keyboard model in menus, footers, and the future function-key bar so power features are visible without reading docs first
- Notes:
- Shortcut hints should appear where decisions happen.
- The app should not require memorizing external docs to use core flows.
- This should consolidate the current shortcut backlog into visible product behavior.

### ITEM_023 — Pane Sync and Mirror Navigation

- Status: `PLANNED`
- Phase: `1`
- Theme: multi-panel workflows
- CommanderStyle inspiration: source-target navigation coordination
- many-panelz direction: allow linked navigation between related panels without weakening independent tab workflows
- Notes:
- Sync should be explicit and reversible.
- The feature must work for sibling panels in a many-panel layout, not only a classic two-pane pair.
- Visual cues should show when panels are linked.

### ITEM_024 — Open in many-panelz and Open in Explorer Workflow

- Status: `PARTIAL`
- Phase: `1`
- Theme: context actions
- CommanderStyle inspiration: fast handoff from one file-management surface to another
- many-panelz direction: make it easy to open folders in a new app window, a new tab, or system Explorer without breaking the current many-panel session
- Notes:
- The app already ships Explorer handoff actions and strong target-pane opening/mirroring flows.
- The missing piece is direct open-selected-folder-in-new-window and open-selected-folder-in-new-tab behavior from the file-list context.
- This item should emphasize fast workspace branching, not just more shell-launch variants.

### ITEM_048 — Visible Git Branch and Dirty Surface

- Status: `PARTIAL`
- Phase: `1`
- Theme: contextual workflows
- CommanderStyle inspiration: repository-aware file managers that surface branch and dirty state near the active path
- many-panelz direction: expose repository state in panel or tab chrome without turning the app into a full Git client
- Notes:
- The app already detects Git roots, reads the current branch, and resolves remote-origin URLs for context actions.
- The remaining work is to show lightweight branch and dirty/clean state in panel chrome or tab chrome and provide a direct handoff into `git-statuz`.
- File-level repo overlays remain future work under `ITEM_034`; this item is about high-value chrome-level visibility first.

## Phase 2

Phase 2 deepens workflow power once the phase-1 interaction model is stable.
The focus is on tabs, per-folder memory, structured compare and selection flows,
and stronger workspace persistence for real multi-context usage.

### ITEM_025 — Tab Context Menu and Advanced Tab Workflow

- Status: `PARTIAL`
- Phase: `2`
- Theme: tabs
- CommanderStyle inspiration: duplicate, rename, lock, reopen, and list-based tab workflows
- many-panelz direction: make tabs significantly more powerful because the app multiplies them across many panels
- Notes:
- The app already persists recently closed tabs and supports reopening the last closed tab.
- The remaining work is a real tab context menu with duplicate, rename, lock, copy-to-another-panel, and richer reopen history affordances.
- Any tab list popup should remain fast even with many open tabs across the full layout.

### ITEM_026 — Column Control, Density, and Lightweight View Presets

- Status: `PARTIAL`
- Phase: `2`
- Theme: file list presentation
- CommanderStyle inspiration: dense details mode, tabstop control, and aligned scanning
- many-panelz direction: improve details-mode readability before chasing multiple legacy view modes
- Notes:
- The app already supports fit-columns, column-width alignment across current panel, all panels, and all windows, plus heavier saved workspace views.
- The remaining work is lighter file-list-centric presets, stronger column visibility control, and better dense-mode defaults without requiring full workspace view saves.
- Keep this item focused on scanability and file-list ergonomics rather than introducing new view modes.

### ITEM_027 — Per-Folder View Memory

- Status: `PLANNED`
- Phase: `2`
- Theme: persistence
- CommanderStyle inspiration: folders remembering useful sort and view state
- many-panelz direction: let each tab remember context-sensitive sort and view choices without making the app feel globally sticky
- Notes:
- Sort column, direction, and display mode are the high-value fields.
- Start with session-level memory before worrying about cross-machine portability.
- Build on the lighter view-preset groundwork in `ITEM_026`, not on full saved workspace views alone.
- This should complement, not fight, explicit user changes.

### ITEM_028 — Compare, Branch, and Structured Selection Workflows

- Status: `PLANNED`
- Phase: `2`
- Theme: power workflows
- CommanderStyle inspiration: compare-oriented lists, branch views, and structured marking tools
- many-panelz direction: add high-value compare and branch workflows only where they support real multi-panel file management
- Notes:
- Focus on workflows that expose differences or gather related files.
- Keep results navigable inside the existing panel model.
- Avoid features that require a separate quasi-database UI just to function.

### ITEM_029 — Footer Aggregates Beyond Size

- Status: `PARTIAL`
- Phase: `2`
- Theme: status visibility
- CommanderStyle inspiration: richer aggregate summaries for the current marked set
- many-panelz direction: extend the panel footer with counts and aggregate signals that remain compact enough for many simultaneous panels
- Notes:
- File count, directory count, size totals, pending-folder-size counts, and free-space text are already present in the shipped footer baseline.
- The remaining work is optional higher-order aggregates and active-work summaries that stay compact enough for dense multi-panel layouts.
- Expensive aggregates must remain asynchronous and should not regress navigation responsiveness.

### ITEM_030 — Named Workspace and Tab Sessions

- Status: `PARTIAL`
- Phase: `2`
- Theme: workspace state
- CommanderStyle inspiration: saving sets of tabs or work contexts for later reuse
- many-panelz direction: treat saved sessions as first-class multi-panel workspace snapshots, not just startup restore
- Notes:
- The app already restores startup session state, persists recently closed tabs, and supports named saved views for heavier workspace snapshots.
- The remaining work is clearer session vocabulary, lighter named tab/workspace snapshots, and explicit open-in-new-window restore flows.
- Keep session management lightweight and visible instead of burying it behind only one heavyweight save/restore model.

### ITEM_047 — First-Run Workspace Onboarding and Tool Detection

- Status: `PLANNED`
- Phase: `2`
- Theme: onboarding
- CommanderStyle inspiration: practical first-run setup flows that help the user reach a productive baseline quickly
- many-panelz direction: guide users through roots, startup layout, and tool-path setup without turning the app into a wizard-driven product
- Notes:
- Cover initial roots, startup layout choice, terminal/editor/Git-tool path detection, and optional starter bookmarks.
- Only show automatically on first run or when the user explicitly reopens setup from the UI.
- Reuse the workspace’s existing widget-identity and setup-dialog conventions rather than inventing a separate UI style.

### ITEM_031 — Visual Role Cues for Active, Target, and Related Panels

- Status: `PARTIAL`
- Phase: `2`
- Theme: many-panel identity
- CommanderStyle inspiration: obvious source-target awareness during operations
- many-panelz direction: strengthen role cues across active, target, synced, and related panels in an N-panel layout
- Notes:
- Active and target tinting already exist and should be treated as the shipped baseline.
- The remaining work is to introduce clearer related, synced, and operation-role cues without overwhelming the file lists.
- This item should refine the visual language introduced in `ITEM_019`, not duplicate it.

### ITEM_032 — Saved Filters and Search Workflows

- Status: `PLANNED`
- Phase: `2`
- Theme: filtering
- CommanderStyle inspiration: reusable file filters and fast scoped searches
- many-panelz direction: save and reuse real file-management filters without drifting toward an embedded shell or command model
- Notes:
- Saved filters should be easy to reapply from the current panel.
- Search results should stay navigable inside the panel model.
- This item starts after `ITEM_021` provides a stronger inline-filter baseline; it should not absorb the fast-filter surface work.

### ITEM_033 — Export and Import Full App Configuration

- Status: `PLANNED`
- Phase: `2`
- Theme: portability
- CommanderStyle inspiration: portable configuration for power users
- many-panelz direction: let users move a tuned many-panel workspace setup between machines without manually copying settings files
- Notes:
- Include UI settings, operational settings, bookmarks, and future saved sessions.
- Keep the export readable and versioned.
- Machine-specific values should be handled defensively on import.

### ITEM_034 — Repo-Aware Overlays and Signals

- Status: `PARTIAL`
- Phase: `2`
- Theme: contextual workflows
- CommanderStyle inspiration: file list cues that expose repository or content state
- many-panelz direction: add lightweight overlays only when they strengthen the current panel’s decision-making and do not clutter dense layouts
- Notes:
- Git context detection, branch parsing, and remote parsing already exist and feed the dynamic Context menu.
- Chrome-level branch/dirty visibility is tracked in `ITEM_048`; this item is the follow-up for optional file-list overlays and deeper repo-aware signals.
- These signals should remain optional and density-conscious so they help scanning instead of turning the list into noise.

### ITEM_035 — Checkbox-Assisted Marking Column

- Status: `PLANNED`
- Phase: `2`
- Theme: accessibility
- CommanderStyle inspiration: alternative marking affordances for touch or non-modifier workflows
- many-panelz direction: provide an optional assistive marking surface without replacing the explicit mark model
- Notes:
- This should stay optional and density-aware.
- The underlying mark model must remain the same.
- It is only worth doing if it improves usability for touch and accessibility cases.

### ITEM_036 — Recent Files and Virtual Collection Views

- Status: `PLANNED`
- Phase: `2`
- Theme: alternate navigation
- CommanderStyle inspiration: fast access to reusable or non-folder result sets
- many-panelz direction: introduce virtual collections only where they genuinely speed file-management workflows across many panels
- Notes:
- Recent files is the most compelling first collection.
- Virtual collections must still behave like navigable panels, not separate apps.
- They should not displace real filesystem navigation as the main product identity.

## Phase 3

Phase 3 is selective expansion. These items may add value, but they should only
land after the core many-panel commander loop is unmistakably strong.

### ITEM_037 — Thumbnail and Media-Oriented Alternate Views

- Status: `PLANNED`
- Phase: `3`
- Theme: alternate views
- CommanderStyle inspiration: optional thumbnail-style visual browsing
- many-panelz direction: add alternate views only when they still support efficient work inside a many-panel layout
- Notes:
- Thumbnail mode should remain optional, not the default.
- The details view remains the core experience.
- Performance and density matter more than visual flourish.

### ITEM_038 — Metadata Columns and Rich File Attributes

- Status: `PLANNED`
- Phase: `3`
- Theme: file list presentation
- CommanderStyle inspiration: rich file details and custom columns for domain-specific workflows
- many-panelz direction: expose metadata only when it improves real operational decisions in the dense details view
- Notes:
- Start with image or media metadata that has practical value.
- Metadata loading must stay asynchronous.
- Columns should feel like details-view extensions, not a separate data app.

### ITEM_039 — Advanced Tree or Alternate Navigation Surfaces

- Status: `PLANNED`
- Phase: `3`
- Theme: navigation
- CommanderStyle inspiration: tree and alternate directory browsing surfaces
- many-panelz direction: only add tree-like surfaces if they complement the existing panel model rather than competing with it
- Notes:
- This is deliberately later-stage work.
- Any tree surface must justify itself in a many-panel UI.
- The product should not drift into tree-first navigation by default.

### ITEM_040 — Saved Search Bookmarks and Reusable Virtual Views

- Status: `PLANNED`
- Phase: `3`
- Theme: search workflows
- CommanderStyle inspiration: turning complex search results into reusable entry points
- many-panelz direction: saved searches should behave like reusable workflow shortcuts, not like a general-purpose search platform
- Notes:
- This depends on strong saved-filter and search workflows first.
- Saved searches should remain panel-friendly and quick to re-run.
- The feature should support operational reuse, not query complexity for its own sake.

## Rejected Principles And Features

These items are intentionally excluded so the product does not drift away from
its own goals.

### ITEM_041 — Embedded Command Line

- Status: `REJECTED`
- Phase: `—`
- Theme: shell integration
- CommanderStyle inspiration: command line, command history, and shell-centric workflows
- many-panelz direction: rejected because an embedded command line does not strengthen the app’s core many-panel explorer workflow
- Notes:
- External terminal launch remains sufficient.
- The app should invest in file-management affordances, not shell embedding.
- Shortcut and chrome decisions should not reserve space for an internal command line.

### ITEM_042 — Literal CommanderStyle Product Clone

- Status: `REJECTED`
- Phase: `—`
- Theme: product direction
- CommanderStyle inspiration: exact menus, wording, and product identity mimicry
- many-panelz direction: rejected because the app should adapt useful patterns without impersonating another product
- Notes:
- Borrow behavior where it helps.
- Keep naming and UI structure product-native.
- Preserve the many-panel differentiator as the primary identity.

### ITEM_043 — Two-Panel-Only Assumptions

- Status: `REJECTED`
- Phase: `—`
- Theme: architecture
- CommanderStyle inspiration: a fixed left-right worldview
- many-panelz direction: rejected because any accepted feature must still make sense with 3 or more visible panels
- Notes:
- Left-right wording is acceptable only as shorthand.
- Real behavior should generalize to active, target, related, and linked panels.
- This is a core product discipline, not a minor preference.

### ITEM_044 — Legacy 8.3 Filename Modes

- Status: `REJECTED`
- Phase: `—`
- Theme: legacy compatibility
- CommanderStyle inspiration: DOS-era filename compatibility and display modes
- many-panelz direction: rejected because it does not materially strengthen current file-management workflows
- Notes:
- The product is not targeting legacy DOS compatibility as a differentiator.
- The maintenance cost is not justified by the workflow gain.
- This should stay out unless a strong modern use case appears later.

### ITEM_045 — Brief or Tree Parity as a Default Goal

- Status: `REJECTED`
- Phase: `—`
- Theme: view modes
- CommanderStyle inspiration: reproducing classic brief or tree modes as a parity target
- many-panelz direction: rejected as a default direction because the app should first improve its dense details view and panel-local workflows
- Notes:
- Alternate views may still arrive later when justified.
- The product should not chase view-mode nostalgia as phase-1 identity work.
- Density and clarity in the current primary view matter more.

### ITEM_046 — Remote Client Parity as a Core Product Goal

- Status: `REJECTED`
- Phase: `—`
- Theme: scope discipline
- CommanderStyle inspiration: integrated remote-client breadth as a file-manager identity layer
- many-panelz direction: rejected because remote protocol breadth is not central to the current product thesis
- Notes:
- The backlog should stay focused on local and workspace-oriented multi-panel workflows.
- This avoids diluting attention from panel interaction quality.
- Remote features can be reconsidered only if a future product direction demands them.

This file is the canonical backlog for `many-panelz-explorer`.
Older roadmap files and the shortcut crosswalk remain useful source material,
but backlog curation should happen here.
