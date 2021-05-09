

ARG GITHUB_VERSION=4.33.0
FROM jlongman/mega-linter-pylib:v$GITHUB_VERSION as mega-linter-pylib
FROM nvuillam/mega-linter:v$GITHUB_VERSION


LABEL GITHUB_VERSION=v$GITHUB_VERSION

######################
# Set the entrypoint #
######################
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]

################################
# Installs python dependencies #
################################

COPY megalinter /megalinter
COPY pylib /megalinter/pylib
COPY --from=mega-linter-pylib /root/.local/ /root/.local/
# should be redundant
RUN python /megalinter/setup.py install \
    && python /megalinter/setup.py clean --all \
    && rm -rf /var/cache/apk/*

#######################################
# Copy scripts and rules to container #
#######################################
COPY megalinter/descriptors /megalinter-descriptors
COPY TEMPLATES /action/lib/.automation
