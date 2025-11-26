ARG BUILD_FROM=ghcr.io/home-assistant/{arch}-base:latest
FROM ${BUILD_FROM}

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV VIRTUAL_ENV=/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

# Install runtime dependencies (Alpine base) and isolate Python packages in a venv
RUN apk add --no-cache bash python3 py3-pip py3-virtualenv git \
  && python3 -m venv "${VIRTUAL_ENV}" \
  && pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir py-air-control paho-mqtt PyYAML git+https://github.com/rgerganov/CoAPthon3

WORKDIR /usr/src/app

# Copy app
COPY coap-air-purifier-2-mqtt.py /usr/src/app/
COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
