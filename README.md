# Orvibo S20 Alexa Integration with IFTTT (On a Raspberry PI)


## Requirements


* A Django compatible database (I'm using MySQL 5.5)
* Python 2.7+
* Orvibo S20 plug(s)

## Installation

I have this installed on a Raspberry Pi 3 with Python 2.7.12, but should work on earlier Python versions.

    cd /srv/
    git clone git@github.com:stuartornum/s20-plug-smart-relay.git
    pip install -r requirements.txt

You'll need to modify the `smart_home_relay/settings.py` with the following:

* `API_KEY` - This is the API Key you'll send in API requests, make it at least 30 characters long
* `SECRET_KEY` - Generate the Django secret key here: http://www.miniwebtool.com/django-secret-key-generator/
* Lines 69 to 72 are the database credentials


Now lets get it running:

    python manage.py createsuperuser
    # Follow the on screen prompts to setup the super user
    # check it's all running
    python manage.py runserver

Go to http://127.0.0.1/smartadmin to confirm

### uWSGI
I've included uWSGI config to get it running

## Thanks to

* Core S20 plug controller https://github.com/glenpp/OrviboS20


