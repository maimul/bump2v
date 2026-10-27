# bump2v in a container, for CI systems that run each job in an image (GitLab CI,
# Bitbucket Pipelines, Jenkins, Woodpecker) and for running it without installing Python:
#   docker run --rm -v "$PWD:/repo" ghcr.io/maimul/bump2v bump2v plan auto
# No ENTRYPOINT: CI runners start their own shell in the image.

# A floating tag, so every release is built on the latest Python and Alpine patches.
# Each published version's image is built once and never rebuilt.
FROM python:3.14-alpine

LABEL org.opencontainers.image.source="https://github.com/maimul/bump2v" \
      org.opencontainers.image.description="Version every file, commit, tag and push in one command" \
      org.opencontainers.image.licenses="MIT"

# The repo is mounted or cloned by another user (the CI runner), and git refuses to
# work in a repository it doesn't own unless it's told the directory is safe.
RUN apk add --no-cache git openssh-client \
 && git config --system --add safe.directory '*'

COPY . /tmp/bump2v
RUN pip install --no-cache-dir /tmp/bump2v && rm -rf /tmp/bump2v

WORKDIR /repo
CMD ["bump2v", "--help"]
