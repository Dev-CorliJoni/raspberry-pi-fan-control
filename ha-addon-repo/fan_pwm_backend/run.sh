# ha-addon-repo/fan_pwm_backend/run.sh
#!/usr/bin/with-contenv bashio
set -e

export DATA_DIR="/data"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Default PWM config. Adjust via add-on environment if needed.
export PWM_PIN="${PWM_PIN:-33}"
export PWM_CHIP="${PWM_CHIP:-pwmchip0}"
export PWM_CHANNEL="${PWM_CHANNEL:-1}"
export PWM_FREQUENCY_HZ="${PWM_FREQUENCY_HZ:-25000}"

exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 80