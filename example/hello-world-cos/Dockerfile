# syntax=docker/dockerfile:1.4@sha256:9ba7531bd80fb0a858632727cf7a112fbfd19b17e94c4e84ced81e24ef1a0dbc

FROM mirror.gcr.io/mambaorg/micromamba:2.3-debian13-slim@sha256:3f92db74f6780f60c9a2c6d983c76360a1d4cfdcb597395ab9e64747f067b15b

ENV DEBIAN_FRONTEND=noninteractive


# Revert to being root temporarily
USER 0
# Install base dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean \
    && echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' | tee /etc/apt/apt.conf.d/keep-cache \
    && apt-get -qq update -y \
    && apt-get -qq install --no-install-recommends -y curl git ca-certificates git python3-pip build-essential gnupg

RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean \
    && apt-get -qq update -y \
    && apt-get -qq install --no-install-recommends -y google-cloud-cli

# Create mount path used by gcsfuse to mount data
RUN mkdir -p /mnt/ && chown mambauser:mambauser /mnt/ && chmod g+w /mnt/
VOLUME /mnt/share

# Back to non-root to install dependencies
USER mambauser


COPY environment.yml .
RUN micromamba env create --download-only --yes -f ./environment.yml
RUN micromamba env create --yes -f ./environment.yml


COPY docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
