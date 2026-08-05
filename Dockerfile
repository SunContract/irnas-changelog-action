FROM python:3.12-alpine

WORKDIR /action
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

ENTRYPOINT ["irnas-changelog-action", "--github-action"]
