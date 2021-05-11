# Rider API Service (RAS)

## Set up
```shell
# Create a virtual environment (python version: 3.9.X):
$ pyenv install 3.9.x
$ pyenv virtualenv 3.9.x ras
$ pyenv activate ras


# Install packages:
$ poetry install --no-root


# Install precommit hooks:
$ pre-commit install --install-hooks -t pre-commit -t prepare-commit-msg -t commit-msg


# Set environment variables:
$ echo 'DJANGO_SECRET_KEY=...' > .env
```

## Usage
```shell
$ uvicorn config.asgi:application
```
