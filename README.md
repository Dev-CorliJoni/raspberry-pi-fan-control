# Raspberry Pi Fan PWM Backend

## Overview

This service provides:
- Hardware PWM fan control via Linux sysfs: `/sys/class/pwm/`
- Temperature sensors via sysfs:
  - `/sys/class/thermal/thermal_zone*/temp`
  - `/sys/class/hwmon/hwmon*/temp*_input`
- FastAPI endpoints to manage:
  - Sensors
  - Fan curves (multiple per sensor, one active per sensor)
  - Global settings (units, smoothing, hysteresis, kickstart, safety)
  - Status and setup guidance (`/setup/*`)

Control rule:
- For each enabled sensor: compute duty from its active curve (linear interpolation).
- Target duty is the maximum across all sensors.
- Safety overrides always win (e.g., hard-limit temperature or read failures -> 100%).

---

## Quick Start (Docker Compose)

1) Build and run:
```bash
docker compose up -d --build
```

2) Open:
- API docs: `http://<pi-ip>:<mapped-port>/docs`
- Status: `http://<pi-ip>:<mapped-port>/status`
- Setup wizard: `http://<pi-ip>:<mapped-port>/setup/next-step`

---

## Hardware PWM Setup (GPIO13 / Pin 33)

### Why a reboot might be needed
The container can configure PWM at runtime if the sysfs PWM device exists and is mapped to the correct pin.
If the PWM overlay / pinmux is not enabled by the OS at boot, the container cannot reliably create that mapping without host changes + reboot.

### Raspberry Pi OS / Debian (Bookworm)
Config file is often:
- `/boot/firmware/config.txt`

Add a PWM overlay that maps PWM channels to GPIO12/GPIO13:

```ini
dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
```

Reboot afterwards.

Notes:
- GPIO13 (Pin 33) is commonly PWM1 (sysfs channel `1`) when using the overlay above.
- You can verify PWM sysfs:
  ```bash
  ls -l /sys/class/pwm
  find /sys/class/pwm -maxdepth 3 -type f
  ```

### Home Assistant OS (HAOS)
HAOS uses a boot mount at:
- `/mnt/boot/config.txt`

Add the same overlay line and reboot the host:
```ini
dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
```

---

## Permissions

### docker-compose
The container needs:
- Read access to: `/sys/class/thermal`
- Read/write access to: `/sys/class/pwm`

If PWM writes fail, the service will keep running, log the reason, and `/setup/next-step` will explain what is missing.

### Home Assistant Add-on
Depending on HAOS version and restrictions, writing to `/sys/class/pwm` may require elevated permissions (e.g., `full_access` / `privileged`).
The service will detect missing write access and tell you the next step through `/setup/next-step`.

---

## Default behavior

Defaults are persisted in SQLite and can be changed via `/settings`:
- Loop interval: 1s
- Temperature smoothing window: 15s moving average
- Temperature hysteresis: 1.0°C
- Kickstart: enabled (only for 0% -> >0% transitions), 100% for 300ms
- Hard limit: 80.0°C with a 5.0°C margin -> force 100%
- Fail-safe: 100% on sensor errors

---

## Troubleshooting

Use:
- `/setup/status` and `/setup/next-step`
- Container logs

Useful host checks:
```bash
ls -l /sys/class/thermal/thermal_zone*/temp
ls -l /sys/class/pwm
```

