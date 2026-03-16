# 🏡 Dreame & MOVA Lawn Mower Integration for Home Assistant

[![GitHub Release](https://img.shields.io/github/v/release/antondaubert/dreame-mower?style=flat-square)](https://github.com/antondaubert/dreame-mower/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square)](https://hacs.xyz/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

A Home Assistant integration for **Dreame** and **MOVA** robotic lawn mowers. Control your mower, view maps, track mowing sessions, and monitor battery status directly from Home Assistant.

*If this integration saves you time, consider to [buy me a ☕](https://buymeacoffee.com/antondaubert).*

### Disclaimer
This is an **community-developed integration** for interoperability with Home Assistant. It is not affiliated with or supported by Dreame Technology or MOVA.

Provided "as-is" under the MIT License for personal, non-commercial use with devices you own. Use at your own risk.

## Current Features
- **Live Maps** - See your mower's location and coverage in real-time
- **Session Tracking** - Current and previous mowing sessions  
- **Session History** - Keep track of past mowing activities
- **Remote Control** - Start, pause, stop, and dock your mower
- **Zone Selection** - Mow specific zones of your lawn
- **Battery Status** - Current battery level and charging info
- **Mowing Progress** - Coverage percentage and session duration
- **Do Not Disturb** - View quiet hours settings
- **Notifications** - Status updates and error alerts

*Have suggestions? Check out [Discussions](https://github.com/antondaubert/dreame-mower/discussions)*

## Zone Selection

If your map contains multiple named zones you can target individual zones from the HA UI or from automations.

### UI — Zone Select dropdown

A **Zone Select** entity is created alongside the mower entity. Use it to pick which zone to mow before pressing Start:

1. Open your mower dashboard card (or go to **Settings → Devices & Services → your mower**).
2. Find the **Zone Select** entity and choose a zone from the dropdown.
3. Press the normal **Start** button — the mower will mow only the selected zone.
4. To return to full-lawn mowing, set the dropdown back to **All zones** before pressing Start.

> **Note:** Zone names are populated from the device map. If the list is empty wait for the next automatic update.

### Automations — `start_mowing_zones` service

For automations (e.g. "mow the front lawn every Monday") you can call the `dreame_mower.start_mowing_zones` service directly. This also supports mowing **multiple zones in one session**.

```yaml
service: dreame_mower.start_mowing_zones
target:
  entity_id: lawn_mower.my_mower
data:
  zone_ids: [2]          # single zone
  # zone_ids: [1, 3]     # or multiple zones at once
```

Zone IDs are visible in the mower entity's state attributes (`zones` list) in **Developer Tools → States**, or via the map camera entity after the first map load.

## Installation

1. Ensure [HACS](https://hacs.xyz/) is installed
2. Navigate to HACS → Integrations
3. Click ⋮ → Custom repositories  
4. Add: `https://github.com/antondaubert/dreame-mower`
5. Category: Integration
6. Settings → Devices & Services → Add Integration → "Dreame Mower"

## Community & Support

- **Discussions**: Questions and ideas → [GitHub Discussions](https://github.com/antondaubert/dreame-mower/discussions)
- **Issues**: Bug reports and feature requests → [GitHub Issues](https://github.com/antondaubert/dreame-mower/issues)

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments & Development

This integration was developed through community collaboration for the purpose of achieving interoperability with Home Assistant. It builds upon:

- [Benedikt Hübschen's](https://github.com/bhuebschen/dreame-mower) original mower integration
- Insights from [Tasshack's](https://github.com/Tasshack/dreame-vacuum) vacuum integration
- Protocol analysis and testing by the Home Assistant community

Special thanks to the entire Home Assistant community for continuous support and feedback!

---

*Happy mowing! 🌱*