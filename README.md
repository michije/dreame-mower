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
- **Map Awareness** - Inspect known maps, zones, contours, and active task metadata
- **Battery Status** - Current battery level and charging info
- **Mowing Progress** - Coverage percentage and session duration
- **Do Not Disturb** - View quiet hours settings
- **Notifications** - Status updates and error alerts

*Have suggestions? Check out [Discussions](https://github.com/antondaubert/dreame-mower/discussions)*

## UI Elements

The current release does not expose map, zone, or edge selection controls in the Home Assistant UI yet.

### TODO: Hierarchical Mowing UI

The intended UI flow is:

1. Select the active map.
2. Pick a mowing scenario: all-area, edge, zone, spot, or manual.
3. If edge or zone is selected, choose one or more contours or zones.
4. If spot is selected, define the target rectangle.
5. Manual control is expected to depend on Bluetooth and remains further out in the roadmap.

The device layer already tracks map metadata and verified mowing modes so this UI can be added later without reworking the protocol layer again.

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