# ha-addon-repo/fan_pwm_backend/README.md
# Raspberry pi fan conrol Add-on

After installation:
- Open Web UI: `http://<homeassistant>:8099/docs`
- Setup hints: `/setup/next-step`

If `/setup/next-step` says PWM sysfs is missing:
- Edit `/mnt/boot/config.txt` on HAOS and add:
  `dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4`
- Reboot host

If `/setup/next-step` says PWM is not writable:
- Depending on HAOS version and restrictions, you may need to enable add-on permissions
  (e.g. `full_access: true` in the add-on config) and restart the add-on.

All persistent data is stored in `/data/app.db`.