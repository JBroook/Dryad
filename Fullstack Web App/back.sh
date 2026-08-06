#!/bin/bash

cd backend || exit
pipenv run python manage.py runserver