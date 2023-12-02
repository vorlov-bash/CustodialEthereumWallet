FROM python:3.10.9


ENV POETRY_VERSION=1.4.2 \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VIRTUALENVS_IN_PROJECT=0 \
    POETRY_VIRTUALENVS_CREATE=0


RUN apt-get update -y \
    && apt-get install -y libxslt-dev libxml2-dev screen rsync \
    && pip install "poetry==$POETRY_VERSION"


COPY poetry.lock pyproject.toml ./
RUN poetry install --without dev

COPY . /app
WORKDIR /app
