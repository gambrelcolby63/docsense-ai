FROM python:3.12-bookworm

# Codespaces image: Python, Node, and Tesseract so both apps run in one container.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        tesseract-ocr \
        tesseract-ocr-eng \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY --from=node:22-bookworm /usr/local/bin/node /usr/local/bin/node
COPY --from=node:22-bookworm /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -sf /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -sf /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

WORKDIR /workspace
