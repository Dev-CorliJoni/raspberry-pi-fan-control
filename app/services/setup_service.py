# app/services/setup_service.py
import os
import re
from typing import Dict, Any, Optional


class SetupService:
    def get_setup_status(self) -> Dict[str, Any]:
        os_info = _read_os_release()
        running_in_ha = _is_home_assistant_addon_env(os_info)

        thermal_ok = os.path.exists("/sys/class/thermal/thermal_zone0/temp")

        pwm_root = "/sys/class/pwm"
        pwm_chip_dirs = _list_pwmchips(pwm_root)
        pwm_ok = len(pwm_chip_dirs) > 0

        writable_pwm = _is_writable_pwm(pwm_root)

        return {
            "os": os_info,
            "running_in_home_assistant_addon": running_in_ha,
            "thermal_ok": thermal_ok,
            "pwm_sysfs_present": pwm_ok,
            "pwm_write_access": writable_pwm,
            "pwmchips": pwm_chip_dirs,
        }

    def get_next_step(self, setup_status: Dict[str, Any]) -> str:
        running_in_ha = bool(setup_status.get("running_in_home_assistant_addon"))

        if not setup_status.get("thermal_ok"):
            return "Temperature sysfs not found. Ensure /sys/class/thermal is mounted and thermal_zone0 exists."

        if not setup_status.get("pwm_sysfs_present"):
            return self._explain_enable_pwm_overlay(running_in_ha=running_in_ha)

        if not setup_status.get("pwm_write_access"):
            if running_in_ha:
                return (
                    "PWM sysfs exists but is not writable. In Home Assistant add-on, you likely need elevated permissions "
                    "(e.g., full access / privileged depending on HAOS restrictions). Enable it for the add-on and restart, "
                    "then re-check /setup/status."
                )
            return (
                "PWM sysfs exists but is not writable. In docker-compose, ensure /sys/class/pwm is mounted read-write "
                "and the container has sufficient permissions. If needed as a fallback, run with higher privileges, "
                "but the service tries to work without privileged by default."
            )

        return "Setup looks OK. Use /docs to configure sensors and curves. If the fan does not respond, check PWM chip/channel mapping."

    def _explain_enable_pwm_overlay(self, running_in_ha: bool) -> str:
        if running_in_ha:
            return (
                "PWM sysfs is missing. On Home Assistant OS, edit /mnt/boot/config.txt and add an overlay like:\n"
                "  dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4\n"
                "Then reboot the host. After reboot, /sys/class/pwm should expose pwmchip entries."
            )
        return (
            "PWM sysfs is missing. On Raspberry Pi OS / Debian, edit your boot config.txt "
            "(often /boot/firmware/config.txt on Bookworm) and add:\n"
            "  dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4\n"
            "Then reboot. After reboot, /sys/class/pwm should expose pwmchip entries."
        )


def _list_pwmchips(pwm_root: str) -> list[str]:
    try:
        if not os.path.isdir(pwm_root):
            return []
        out = []
        for name in os.listdir(pwm_root):
            if re.match(r"^pwmchip\d+$", name):
                out.append(name)
        return sorted(out)
    except Exception:
        return []


def _is_writable_pwm(pwm_root: str) -> bool:
    # We consider PWM writable if at least one pwmchip export file is writable.
    try:
        if not os.path.isdir(pwm_root):
            return False
        for name in os.listdir(pwm_root):
            if not re.match(r"^pwmchip\d+$", name):
                continue
            export_path = os.path.join(pwm_root, name, "export")
            if os.path.exists(export_path) and os.access(export_path, os.W_OK):
                return True
        return False
    except Exception:
        return False


def _read_os_release() -> Dict[str, str]:
    path = "/etc/os-release"
    out: Dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = (line or "").strip()
                if not line or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"')
    except Exception:
        pass
    return out


def _is_home_assistant_addon_env(os_info: Dict[str, str]) -> bool:
    # Common in HA add-ons: SUPERVISOR_TOKEN exists.
    if os.getenv("SUPERVISOR_TOKEN"):
        return True
    # HAOS often reports Alpine Linux.
    if (os_info.get("ID") or "").lower() == "alpine":
        return True
    # Another common path on HAOS:
    if os.path.exists("/run/supervisor"):
        return True
    return False