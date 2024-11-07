#!/bin/sh

flask db upgrade

exec qunicorn --bind 0.0.0.0:80 "app:create_app()"