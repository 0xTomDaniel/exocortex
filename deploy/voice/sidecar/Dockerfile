FROM debian:bookworm-slim

ARG CODEX_VERSION=0.153.1
ARG INSTALLER_SHA256=ba92dd27e5c06f0d3bbc58bfa4b9cfb6599cd2742fbb1f92a2765e6c07dedb5a

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates curl git procps python3 tar util-linux \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 --shell /bin/bash codex

USER codex
ENV HOME=/home/codex
ENV PATH=/home/codex/.local/bin:${PATH}
WORKDIR /workspace

RUN curl -fsSL https://chatgpt.com/codex/install.sh -o /tmp/codex-install.sh \
    && echo "${INSTALLER_SHA256}  /tmp/codex-install.sh" | sha256sum -c - \
    && sh /tmp/codex-install.sh --release "${CODEX_VERSION}" \
    && rm /tmp/codex-install.sh \
    && codex --version

USER root
RUN mkdir -p /opt/codex-seed \
    && cp -a /home/codex/.codex/. /opt/codex-seed/ \
    && chown -R codex:codex /opt/codex-seed
USER codex

COPY --chmod=0755 --chown=codex:codex entrypoint.sh /usr/local/bin/exo-codex-entrypoint
ENTRYPOINT ["/usr/local/bin/exo-codex-entrypoint"]
