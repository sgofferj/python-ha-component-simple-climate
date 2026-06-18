# Simple Climate

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![mypy checked](https://img.shields.io/badge/mypy-checked-3178C6.svg)](https://mypy-lang.org/)
[![pylint](https://img.shields.io/badge/pylint-10%2F10-2ECC71.svg)](https://github.com/pylint-dev/pylint)
[![tests](https://img.shields.io/badge/tests-28%20passed-2ECC71.svg)](tests/)

A Home Assistant climate component with separate heating and cooling switch effectors, optional outdoor temperature comparison, and configurable hysteresis.

## Features

- **Climate entity** — heat, cool, and off modes with separate heat/cool setpoints via a range slider
- **Dual effectors** — separate switches for heating and cooling; the opposite effector is always turned off for safety
- **Fully UI-configured** — no YAML, set up entirely via the Home Assistant integration flow
- **Temperature sensors** — pick any temperature sensor for inside and optional outside
- **Mode selection** — independently enable or disable heat/cool modes (heat-only, cool-only, or both)
- **Hysteresis** — configurable deadband around target temp to prevent rapid cycling
- **Outside temperature check** — per-mode toggles: only cool when outside is cooler than inside, or only heat when outside is warmer
- **Safety shutdown temperatures** — configurable hard limits that trigger a persistent notification, disable all effectors, and lock the controller until manually reset

## Installation

### HACS (recommended)

1. Add this repository as a custom repository in HACS.
2. Search for "Simple Climate" and install.
3. Restart Home Assistant.

### Manual

1. Copy `custom_components/simple_climate/` to your Home Assistant `custom_components/` directory.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for "Simple Climate" and select it.
3. Fill in:
   - **Name** — friendly name for the climate entity
   - **Inside temperature sensor** — entity that reports indoor temperature
   - **Heating switch** — switch to turn on for heating
   - **Cooling switch** — switch to turn on for cooling
   - **Heat setpoint** — desired temperature for heating
   - **Cool setpoint** — desired temperature for cooling
   - **Default mode** — cool, heat, or off
   - **Outside temperature sensor** (optional) — for the outside check
   - **Hysteresis** — deadband in °C (default 0.5)
   - **Enable heat / cool mode** — turn modes on or off independently
   - **Check outside temp before heating / cooling** — only run when outside conditions help
   - **Heat safety max temp** — if inside temp exceeds this, emergency shutdown (0 = off)
   - **Cool safety min temp** — if inside temp drops below this, emergency shutdown (0 = off)

After setup, you can reconfigure any option via **Configure** on the integration card.

## How it works

### Cooling (uses the cool setpoint)
- Cool switch turns **on** when inside temp > cool setpoint + hysteresis/2
- Cool switch turns **off** when inside temp < cool setpoint - hysteresis/2
- Heat switch is kept **off**

### Heating (uses the heat setpoint)
- Heat switch turns **on** when inside temp < heat setpoint - hysteresis/2
- Heat switch turns **off** when inside temp > heat setpoint + hysteresis/2
- Cool switch is kept **off**

### Outside check (optional, per mode)
- **Cooling**: cool switch only activates if outside temp is lower than inside
- **Heating**: heat switch only activates if outside temp is higher than inside

### Safety shutdown temperatures
- Set a **heat safety max temp** — if the indoor sensor reads higher, both effectors switch off, a persistent notification is raised, and the controller enters lockout until the user changes any HVAC mode
- Set a **cool safety min temp** — same behavior but for the lower bound
- Set to **0** to disable each limit
- Lockout survives HA restarts via state restoration

### Mode toggles
- **Enable heat only** — the climate UI only shows off and heat
- **Enable cool only** — the climate UI only shows off and cool
- **Enable both** — the climate UI shows off, heat, and cool

## Disclaimer

This integration has been quality-checked with **black**, **mypy**, **pylint**, and **28 automated tests** covering all core logic paths — hysteresis deadbands, sensor unavailability, outside-temperature checks, dual-effector safety interlocks, dynamic mode toggling, setpoint changes, and config/options fallback.

However, controlling physical equipment (heaters, coolers, pumps, fans) always carries inherent risk. Despite thorough testing, a software bug, sensor failure, network issue, or misconfiguration could theoretically cause an effector to remain stuck on or off, potentially leading to property damage or safety hazards.

**Use this integration entirely at your own risk.** The author(s) assume no liability for any damage or injury resulting from its use. Always install appropriate hardware-level safety limits (thermal fuses, overflow switches, etc.) and regularly verify correct operation.

## License

MIT
