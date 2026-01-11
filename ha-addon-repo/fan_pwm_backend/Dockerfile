# ha-addon-repo/fan_pwm_backend/Dockerfile
ARG BUILD_FROM
FROM ${BUILD_FROM}

# Home Assistant add-on tutorial recommends run.sh using bashio.
# This add-on runs a Python FastAPI app.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python and pip
RUN apk add --no-cache python3 py3-pip

COPY app /app/app
COPY requirements.txt /app/requirements.txt
COPY run.sh /run.sh
COPY README.md /app/README.md

RUN pip3 install --no-cache-dir -r /app/requirements.txt \
  && chmod a+x /run.sh

EXPOSE 80

CMD [ "/run.sh" ]