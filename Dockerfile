FROM python:3.12-alpine

RUN apk add --no-cache git

WORKDIR /action
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

ENTRYPOINT ["irnas-changelog-action", "--github-action"]
