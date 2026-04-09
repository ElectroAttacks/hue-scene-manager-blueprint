# Hue Scene Refresher

> Intelligently refreshes Philips Hue scenes when lights change state, using advanced state transition detection to minimise unnecessary updates.

[![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FElectroAttacks%2Fhue-scene-manager-blueprint%2Fblob%2Fmain%2Fhue-scene-refresher.yaml)

---

## Overview

**Hue Scene Refresher** combines three-state evaluation (`on` / `off` / `partial_on`) with transition-aware targeting so only the required rooms and zones are refreshed — never more, never less.

When any monitored Hue entity changes, a short polling window opens that:

- Repeats every configured interval while additional changes occur
- Collects every Hue light transition into a single evaluation pass
- Provides the full context so room and zone targeting stays accurate

**Minimum Home Assistant version:** `2025.12.4`

---

## Features

| Category | Highlights |
|---|---|
| **Trigger monitoring** | Watches Hue lights, rooms, or zones for `on`/`off` transitions; optional supplemental triggers for attribute changes |
| **Scene activation** | Configurable transition durations for both scene activation and brightness restoration |
| **Dynamic scenes** | Per-group dynamic playback toggle with speed override |
| **Advanced evaluation** | Three-state group assessment, automatic overlapping-zone mapping, per-entity exclusions |
| **Post-refresh hooks** | Custom actions when a group turns off or after every refresh cycle |

---

## Configuration

### Trigger Monitoring & Polling

| Input | Default | Description |
|---|---|---|
| `targets` | — | Hue lights, rooms, or zones to monitor |
| `state_trigger_delay` | `1 s` | Polling interval — also sets the burst-collection window |
| `alternative_triggers` | `[]` | Optional supplemental trigger sources |

### Scene Activation & Brightness Control

| Input | Default | Description |
|---|---|---|
| `transition_time` | `2 s` | Brightness restore duration per light |
| `scene_transition_time` | `4 s` | Scene activation duration |
| `dynamic_scene_speed` | `-1` | Dynamic-effect speed override (`-1` = keep scene default) |
| `targets_with_dynamic_scenes` | `[]` | Groups that activate scenes with `dynamic: true` |

### Advanced Evaluation & Safeguards

| Input | Default | Description |
|---|---|---|
| `ignore_active_effects` | `false` | Count lights running effects as `on` |
| `turn_off_state_excluded_lights` | `true` | Force-off excluded lights that were off in the snapshot |
| `targets_excluded_from_state_check` | `[]` | Lights ignored during state evaluation |
| `targets_excluded_from_brightness_restore` | `[]` | Lights that keep scene brightness after refresh |

### Post-Refresh Automation Hooks

| Input | Default | Description |
|---|---|---|
| `turn_off_actions` | `[]` | Actions executed when a group ends in `off` state |
| `post_activation_actions` | `[]` | Actions executed after every successful refresh |

> **Tip:** Use `repeat.item[0]` for the group `entity_id` and `repeat.item[1]` for its snapshot (`state`, `brightness`, `scene`, `lights`, `zones`) inside hook actions.

---

## Support

If this blueprint is useful to you, consider [sponsoring the project](https://github.com/sponsors/ElectroAttacks). ❤️
