# Keyboard Shortcuts

This document is the authoritative keyboard shortcut inventory for
`many-panelz-explorer`.

It serves two purposes:

- track the current app shortcut surface
- track Total Commander parity against the full reference supplied for this repo task

## Status Meanings

| Status | Meaning |
|---|---|
| `Keep` | Current app behavior is accepted as-is for this TC row. |
| `Add` | Approved future parity target. |
| `Reject` | Explicitly not wanted. |
| `Not implemented` | Present in TC, but absent or not yet accepted in the app. |

## Total Commander Crosswalk

### Core Function Keys

| TC Shortcut | TC Action | Current App Shortcut | App Equivalent | Status | Notes |
|---|---|---|---|---|---|
| `F1` | Help | `F1` | Show help dialog | `Keep` | Direct match. |
| `F2` | Reread source window | `F2` | Refresh all visible panes | `Keep` | App refresh is broader than TC source-pane reread. |
| `F3` | List files | `F3` | View current item | `Keep` | Direct viewer-style match. |
| `F4` | Edit files | `F4` | Edit current item | `Keep` | Direct match. |
| `F5` | Copy files | `F5` | Copy selection to target pane | `Keep` | Direct match. |
| `F6` | Rename or move files | `F6` | Move selection to target pane | `Keep` | Move matches; in-place rename is separate in TC. |
| `F7` | Create directory | `F7` | Create directory | `Keep` | Direct match. |
| `F8 or DEL` | Delete files | `F8`, `Delete` | Delete selection | `Keep` | Direct match. |
| `F9` | Activate menu above source window | `F9` | Open terminal in active tab | `Not implemented` | `F9` is already used differently in the app. |
| `F10` | Activate left menu or leave menu | `F10` | Focus main menu bar | `Keep` | Similar menu-focus behavior, not pane-specific. |
| `Alt+F1` | Change left drive | `Alt+F1` | Open active-tab root picker | `Keep` | Root picker is the app equivalent of drive switching. |
| `Alt+F2` | Change right drive | None | No target-pane root picker | `Reject` | Explicitly not wanted. |
| `Alt+F3` | Alternate viewer | `Alt+F3` | Open dedicated viewer | `Keep` | Direct match. |
| `Alt+Shift+F3` | Internal viewer without plugins | None | No equivalent | `Not implemented` | No Lister-style variant. |
| `Alt+F4` | Exit or minimize | `Alt+W`, `Ctrl+Q`, `Alt+X`, `Shift+Esc` | Close window, exit app, minimize managed windows | `Not implemented` | Equivalent behaviors exist, but not on the TC key. |
| `Alt+F5` | Pack selected files | `Alt+F5` | Open archive pack dialog | `Keep` | Opens the queued pack dialog with WinRAR or 7-Zip backend selection. |
| `Alt+Shift+F5` | Move to archive | None | No equivalent | `Not implemented` | Archive move flow is absent. |
| `Alt+F6` | Unpack archive under cursor | None | No equivalent | `Not implemented` | Archive extraction shortcut is absent. |
| `Alt+F7` | Find | `Alt+F7` | Search active path in Everything | `Keep` | App uses Everything when configured and available. |
| `Alt+Shift+F7` | Find in separate process | None | No equivalent | `Not implemented` | No equivalent. |
| `Alt+F8` | Command-line history | None | No equivalent | `Not implemented` | No command line in the app. |
| `Alt+F9` | Same as `Alt+F6` | `Alt+F9` | Open archive unpack dialog | `Keep` | Opens the queued unpack dialog for `.rar` and `.7z` archives. |
| `Alt+Shift+F9` | Test archives | None | No equivalent | `Not implemented` | No archive test flow. |
| `Alt+F10` | Current directory tree dialog | None | No equivalent | `Not implemented` | Root picker exists, but not a current-dir tree dialog on this key. |
| `Alt+F11` | Open left breadcrumb bar | None | No equivalent | `Not implemented` | No shortcut for left-side breadcrumb focus. |
| `Alt+F12` | Open right breadcrumb bar | None | No equivalent | `Not implemented` | No shortcut for right-side breadcrumb focus. |
| `Alt+Shift+F11` | Focus horizontal button bar | None | No equivalent | `Not implemented` | No equivalent. |
| `Alt+Shift+F12` | Focus vertical button bar | None | No equivalent | `Not implemented` | No equivalent. |

### Navigation And History

| TC Shortcut | TC Action | Current App Shortcut | App Equivalent | Status | Notes |
|---|---|---|---|---|---|
| `Alt+Left` | Previous visited dir | `Alt+Left` | Back in history | `Keep` | Direct match. |
| `Alt+Right` | Next visited dir | `Alt+Right` | Forward in history | `Keep` | Direct match. |
| `Alt+Down` | Open visited-dir history | `Alt+Down` | Open panel history menu | `Keep` | Direct match. |
| `Alt+Shift+Down` | Open history without thinning | None | No equivalent | `Not implemented` | No alternate history mode. |
| `Ctrl+PgUp or Backspace` | Change to parent directory | `Backspace`, `Alt+Up`, `Left` | Go to parent directory | `Keep` | `Backspace` matches; `Ctrl+PgUp` is still absent. |
| `Ctrl+PgDn` | Open directory or archive | `Right`, `Enter` | Open selected item | `Keep` | Behavior exists on different keys. |
| `Ctrl+<` | Jump to root directory | `Ctrl+<` | Jump to active root or drive root | `Keep` | Implemented as the same root-jump action as `Ctrl+\`. |
| `Ctrl+\` | Jump to root directory | `Ctrl+\` | Jump to active root or drive root | `Keep` | Implemented through the active panel root navigation. |
| `Ctrl+Left or Ctrl+Right` | Open dir in target window | `Ctrl+Left`, `Ctrl+Right` | Open selected directory in target pane | `Keep` | Falls back to mirroring the current path when the current item is not a directory. |
| `Tab` | Switch between left and right file list | `Tab` | Switch active pane | `Keep` | Direct commander-style pane switching. |
| `Shift+Tab` | Switch between file list and separate tree | `Shift+Tab` | Switch to previous pane | `Keep` | Similar focus movement; no separate tree mode exists. |
| `Enter` | Open dir or run item | `Enter` | Activate current item in file list | `Keep` | Standard tree activation is wired through item activation. |
| `Shift+Enter` | Shell open / alternate enter behaviors | None | No equivalent | `Not implemented` | No dedicated shifted-enter variant. |
| `Alt+Shift+Enter` | Count all subdirectory sizes | None | No equivalent | `Not implemented` | No bulk folder-size calculation shortcut. |
| `Alt+Enter` | Show property sheet | `Alt+Enter` | Show properties dialog | `Keep` | Opens the app properties dialog for the selected or current item. |

### Selection And Context

| TC Shortcut | TC Action | Current App Shortcut | App Equivalent | Status | Notes |
|---|---|---|---|---|---|
| `Insert` | Select file or directory | `Insert` | Toggle current row and advance | `Keep` | Direct commander-style selection flow. |
| `Space` | Select file or directory | `Space` | Toggle current row selection | `Keep` | Direct commander-style selection flow. |
| `Shift+F10` | Show context menu | `Shift+F10` | Open context menu from keyboard | `Keep` | Direct match. |
| `Num +` | Expand selection | None | No equivalent | `Not implemented` | Numeric keypad selection tools are absent. |
| `Num -` | Shrink selection | None | No equivalent | `Not implemented` | Numeric keypad selection tools are absent. |
| `Num *` | Invert selection | None | No equivalent | `Not implemented` | Numeric keypad selection tools are absent. |
| `Num /` | Restore selection | None | No equivalent | `Not implemented` | Numeric keypad selection tools are absent. |
| `Shift+Num +` | Alternate expand selection | None | No equivalent | `Not implemented` | Numeric keypad selection tools are absent. |
| `Shift+Num -` | Alternate shrink selection | None | No equivalent | `Not implemented` | Numeric keypad selection tools are absent. |
| `Shift+Num *` | Alternate invert selection | None | No equivalent | `Not implemented` | Numeric keypad selection tools are absent. |
| `Ctrl+Num +` | Select all | `Ctrl+A` | Select all items in file list | `Keep` | Behavior matches on a different key. |
| `Ctrl+Shift+Num +` | Select all files and folders | None | No equivalent | `Not implemented` | No dedicated variant. |
| `Ctrl+Num -` | Deselect all | None | No equivalent | `Not implemented` | No dedicated deselect-all shortcut. |
| `Ctrl+Shift+Num -` | Deselect all files only | None | No equivalent | `Not implemented` | No dedicated deselect-all variant. |
| `Alt+Num +` | Select same extension | None | No equivalent | `Not implemented` | No extension-based selection shortcut. |
| `Alt+Num -` | Deselect same extension | None | No equivalent | `Not implemented` | No extension-based deselection shortcut. |

### View, Sort, And Display Modes

| TC Shortcut | TC Action | Current App Shortcut | App Equivalent | Status | Notes |
|---|---|---|---|---|---|
| `Shift+F1` | Custom columns view menu | None | No equivalent | `Not implemented` | No custom-columns menu shortcut. |
| `Shift+F2` | Compare file lists | None | No equivalent | `Not implemented` | No compare-lists shortcut. |
| `Shift+F3` | List only file under cursor | None | No equivalent | `Not implemented` | No single-file override shortcut. |
| `Shift+F5` | Copy files with rename in same directory | `Shift+F5` | Copy selection into current directory | `Keep` | Uses the existing rename-on-conflict copy behavior. |
| `Ctrl+Shift+F5` | Create shortcuts of selected files | None | No equivalent | `Not implemented` | No shortcut-creation flow. |
| `Shift+F6` | Rename files in same directory | `Shift+F6` | Rename selected or current item | `Keep` | Direct in-place rename flow. |
| `Shift+F7` | Create target directory with suggested name | `Shift+F7` | Create target directory with suggested name | `Keep` | Creates the folder in the resolved target pane and seeds the prompt from the selected item name when available. |
| `Shift+F8 or Shift+Del` | Alternate delete mode | None | No equivalent | `Not implemented` | Delete backend is configurable, but no shift-specific binding. |
| `Ctrl+F1` | Brief file display | None | No equivalent | `Not implemented` | No view-mode shortcuts. |
| `Ctrl+Shift+F1` | Thumbnails view | None | No equivalent | `Not implemented` | No thumbnails mode shortcut. |
| `Ctrl+F2` | Full file details | None | No equivalent | `Not implemented` | No view-mode shortcuts. |
| `Ctrl+Shift+F2` | Comments view | None | No equivalent | `Not implemented` | No comments view. |
| `Ctrl+F3` | Sort by name | `Ctrl+F3` | Sort by name | `Keep` | Sorts the active file list by the name column. |
| `Ctrl+F4` | Sort by extension | `Ctrl+F4` | Sort by extension | `Keep` | Sorts the active file list by the extension column. |
| `Ctrl+F5` | Sort by date or time | `Ctrl+F5` | Sort by modified date | `Keep` | Uses the modified-date column. |
| `Ctrl+F6` | Sort by size | `Ctrl+F6` | Sort by size | `Keep` | Uses the size column. |
| `Ctrl+F7` | Unsorted | None | No shortcut | `Not implemented` | No unsorted toggle shortcut. |
| `Ctrl+F8` | Display directory tree | None | No equivalent | `Not implemented` | No separate tree-panel shortcut. |
| `Ctrl+Shift+F8` | Cycle tree states | None | No equivalent | `Not implemented` | No tree-state cycling shortcut. |
| `Ctrl+F9` | Print file under cursor | None | No equivalent | `Not implemented` | No print shortcut. |
| `Ctrl+F10` | Show all files | None | No exact equivalent | `Not implemented` | Hidden-file visibility is a menu toggle, not this shortcut. |
| `Ctrl+F11` | Show only programs | None | No equivalent | `Not implemented` | No file-type filter shortcut. |
| `Ctrl+F12` | Show user-defined files | None | No equivalent | `Not implemented` | No user filter shortcut. |

### Tabs, Panels, And Branch Views

| TC Shortcut | TC Action | Current App Shortcut | App Equivalent | Status | Notes |
|---|---|---|---|---|---|
| `Ctrl+Shift+A` | Show list of open tabs | None | No equivalent | `Not implemented` | No tab list menu shortcut. |
| `Ctrl+B` | Directory branch | None | No equivalent | `Not implemented` | No branch view shortcut. |
| `Ctrl+Shift+B` | Branch for selected directories | None | No equivalent | `Not implemented` | No branch view shortcut. |
| `Ctrl+I` | Switch to target directory | None | No equivalent | `Not implemented` | No source-to-target path sync shortcut. |
| `Ctrl+Q` | Show quick view panel | `Ctrl+Q` | Exit application | `Not implemented` | `Ctrl+Q` is already used differently in the app. |
| `Ctrl+Shift+Q` | Separate quick view window | None | No equivalent | `Not implemented` | No quick-view window shortcut. |
| `Ctrl+T` | Open new folder tab and activate it | `Ctrl+T` | New tab in active panel | `Keep` | Direct match. |
| `Ctrl+Shift+T` | Open new folder tab without activation | `Ctrl+Shift+T` | Reopen last closed tab | `Not implemented` | Key is already used differently in the app. |
| `Ctrl+U` | Exchange directories | None | No equivalent | `Not implemented` | No pane-directory swap shortcut. |
| `Ctrl+Shift+U` | Exchange directories and tabs | None | No equivalent | `Not implemented` | No pane-and-tab swap shortcut. |
| `Ctrl+W` | Close active tab | `Ctrl+W` | Close current tab | `Keep` | Direct match. |
| `Ctrl+Shift+W` | Close all open tabs | `Ctrl+Shift+W` | Close active panel | `Not implemented` | Key is already used differently in the app. |
| `Ctrl+Up` | Open dir under cursor in new tab | None | No equivalent | `Not implemented` | No open-in-new-tab shortcut. |
| `Ctrl+Shift+Up` | Open dir under cursor in other window | None | No equivalent | `Not implemented` | No open-in-other-pane shortcut. |
| `Ctrl+Tab` | Jump to next tab | None | No current binding | `Add` | Approved future parity target. |
| `Ctrl+Shift+Tab` | Jump to previous tab | None | No current binding | `Add` | Approved future parity target. |

### Clipboard, Bookmarks, Filter, Search, And Misc

| TC Shortcut | TC Action | Current App Shortcut | App Equivalent | Status | Notes |
|---|---|---|---|---|---|
| `Letter` | Redirect to command line | None | No equivalent | `Not implemented` | No command-line focus model. |
| `Ctrl+A` | Select all | `Ctrl+A` | Select all items in file list | `Keep` | Direct match. |
| `Ctrl+C` | Copy files to clipboard | None | No equivalent | `Not implemented` | No file copy-to-clipboard shortcut. |
| `Ctrl+D` | Open directory hotlist | None | Bookmarks menu exists | `Not implemented` | Bookmark feature exists, binding does not. |
| `Ctrl+F` | Connect to FTP server | `Ctrl+F` | Open inline filter | `Not implemented` | Key is already used differently in the app. |
| `Ctrl+Shift+F` | Disconnect FTP | None | No equivalent | `Not implemented` | No FTP layer. |
| `Ctrl+L` | Calculate occupied space | None | No equivalent | `Not implemented` | No shortcut for size calculation. |
| `Ctrl+M` | Multi-Rename-Tool | None | No equivalent | `Not implemented` | No multi-rename tool shortcut. |
| `Ctrl+Shift+M` | Change FTP transfer mode | None | No equivalent | `Not implemented` | No FTP layer. |
| `Ctrl+N` | New FTP connection | `Ctrl+N` | New window | `Not implemented` | Key is already used differently in the app. |
| `Ctrl+P` | Copy current path to command line | `Ctrl+P` | Copy selected item path or pane path to clipboard | `Keep` | Similar path-copy intent, but no command line exists. |
| `Ctrl+R` | Reread source directory | `Ctrl+R` | Refresh active pane | `Keep` | Similar refresh intent. |
| `Ctrl+S` | Open quick filter dialog | None | Inline filter exists on `Ctrl+F` | `Not implemented` | Filtering exists on a different key and UI. |
| `Ctrl+Shift+S` | Reopen quick filter | None | No equivalent | `Not implemented` | No dedicated last-filter shortcut. |
| `Ctrl+V` | Paste from clipboard | None | No equivalent | `Not implemented` | No file paste shortcut. |
| `Ctrl+X` | Cut files to clipboard | None | No equivalent | `Not implemented` | No cut-to-clipboard shortcut. |
| `Ctrl+Z` | Edit file comment | None | No equivalent | `Not implemented` | No file-comment feature. |
| `AltGr+Letter(s) or Ctrl+Alt+Letter(s)` | Quick search in current directory | None | No equivalent | `Not implemented` | No TC-style typed quick-search binding. |

## App-Specific Shortcuts Outside The TC Reference

These shortcuts are part of the app surface but do not map directly to the TC
reference rows above.

| App Shortcut | Action | Notes |
|---|---|---|
| `Ctrl+Shift+P` | New vertical panel in active row | App-specific pane split shortcut. |
| `Ctrl+H` | New horizontal panel row | App-specific pane split shortcut. |
| `Alt+W` | Close window | App-specific window-management shortcut. |
| `Alt+X` | Exit application | Exit alias retained by the app. |
| `Ctrl+,` | Open settings dialog | App-specific preferences shortcut. |
| `Alt+Up` | Go to parent directory | Extra app navigation alias. |
| `Left` | Go to parent directory from file list | Tree-view navigation shortcut. |
| `Right` | Open selected item from file list | Tree-view navigation shortcut. |
| `F9` | Open terminal in active tab | Conflicts with TC `F9`; intentionally documented here as current app behavior. |
| `Ctrl+Shift+T` | Reopen last closed tab | Not part of TC. |

## Reviewed Parity Decisions

### Kept TC-Aligned Or Near-Aligned Rows

- `F1`, `F3`, `Alt+F3`, `F4`, `Shift+F4`, `F5`, `F6`, `F7`, `F8` / `Delete`
- `Alt+F1`, `Alt+Left`, `Alt+Right`, `Alt+Down`, `Tab`, `Insert`, `Space`
- `Ctrl+A`, `Ctrl+P`, `Ctrl+R`, `Ctrl+T`, `Ctrl+W`, `Shift+Esc`

### Approved Additions

- `Ctrl+Tab` for next tab in the active panel
- `Ctrl+Shift+Tab` for previous tab in the active panel
- `Ctrl+PageDown` as an app alias for next-tab switching
- `Ctrl+PageUp` as an app alias for previous-tab switching

### Explicit Rejections

- `Alt+F2`

## Source Note

The TC crosswalk above is based on the full Total Commander keyboard reference
text supplied for this repository task, not on the shorter public web summary
used in the earlier draft of this document.
