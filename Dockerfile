FROM mcr.microsoft.com/devcontainers/python:1-3.12-bullseye

USER vscode

COPY requirements.txt /tmp/requirements.txt

RUN pip3 install --user -r /tmp/requirements.txt