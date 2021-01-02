##################
# Get base image #
##################
FROM python:3.8-alpine

ARG GITHUB_VERSION=4.20.0
LABEL GITHUB_VERSION=v$GITHUB_VERSION

# APK Packages used by mega-linter pylib
# - this must be a subset of main libraries
#   - what happens if they don't match?
# - this selection is a little shotgun, it appears to work though
RUN apk add --update --no-cache \
    coreutils \
    curl \
    file \
    gcc \
    gnupg \
    icu-libs \
    jq \
    krb5-libs \
    libcurl libintl libssl1.1 libstdc++ \
    libffi-dev \
    linux-headers \
    make \
    musl-dev \
    py3-setuptools \
    readline-dev

################################
# Installs python dependencies #
################################
COPY pylib /pylib
RUN python /pylib/setup.py install --user

###########################
# Get the build arguments #
###########################
ARG BUILD_DATE
ARG BUILD_REVISION
ARG BUILD_VERSION

#################################################
# Set ENV values used for debugging the version #
#################################################
ENV BUILD_DATE=$BUILD_DATE
ENV BUILD_REVISION=$BUILD_REVISION
ENV BUILD_VERSION=$BUILD_VERSION


#########################################
# Label the instance and set maintainer #
#########################################
LABEL com.github.actions.name="Mega-Linter Python Requirements" \
      com.github.actions.description="Python libs for the ultimate linters aggregator to make sure your projects are clean" \
      maintainer="Nicolas Vuillamy <nicolas.vuillamy@gmail.com>" \
      org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.revision=$BUILD_REVISION \
      org.opencontainers.image.version=$BUILD_VERSION \
      org.opencontainers.image.authors="Nicolas Vuillamy <nicolas.vuillamy@gmail.com>" \
      org.opencontainers.image.url="https://nvuillam.github.io/mega-linter" \
      org.opencontainers.image.source="https://github.com/nvuillam/mega-linter" \
      org.opencontainers.image.documentation="https://nvuillam.github.io/mega-linter" \
      org.opencontainers.image.vendor="Nicolas Vuillamy" \
      org.opencontainers.image.description="Lint your code base with GitHub Actions - Python libs"

