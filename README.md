# e2nest - Web-based Media Subjective Testing

[![main](https://github.com/Netflix/e2nest/workflows/main/badge.svg)](https://github.com/Netflix/e2nest/actions?query=workflow%3Amain)

e2nest is a web-based platform for media-centric (video, audio and images) subjective testing. Originally developed at Netflix for internal use, e2nest is now open-sourced under the [BSD 3-clause](LICENSE) license. The name e2nest was derived from "EarnEst NEtflix Subjective Testing".

e2nest is built on the [Django](https://www.djangoproject.com/) web framework. The server end hosts the test media files, a database to log the test scores (currently configured to SQLite, but can be changed to MySQL, PostgreSQL or others), and the business logic to run the tests (e.g. when to serve which media files). The client end is a web browser with proper decoder support on the test subject's computer (for example, for a test with AV1-encoded videos, a proper browser supporting AV1 decoding is required).

For subjective tests with large media files (for example, some tests could require 50GB media files per test session), a special configuration is available where the media files are pre-downloaded and locally hosted on the test subject's computer.

For additional information, refer to our [instruction memo](https://docs.google.com/document/d/123XoaD7jXAypWTSzX4KaVSapaHAeNMq-UUj-WpGpE_0/edit).

## Virtual environment setup

```shell
python3 -m virtualenv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

(```deactivate```: exit the virtual environment)

For all instructions below, assume you have `cd` into `./nest_site`.

## Provide secret key and host address in `nest_site/settings.py`

You need to replace `"PUT_YOUR_SECRET_KEY_HERE"` with your own [secret key](https://docs.djangoproject.com/en/2.2/ref/settings/#secret-key). The secret key is used mostly to provide cryptographic signing for session cookies. This can be any string of your choice, but the longer and more random the better.

If you are hosting your server on a remote host (for example, an AWS EC2 instance) instead of your own computer as a localhost, you need to replace `"PUT_YOUR_SERVER_IP_HERE"` with the remote host's public IP address.

## Database setup

Currently, SQLite3 is configured as the database type.

```python manage.py makemigrations```: create database migration files under `migrations/`.

```python manage.py migrate --run-syncdb```: The migrate command looks at the INSTALLED_APPS setting and creates any necessary database tables according to the migration files.

## Run tests in command line

[tox](https://tox.wiki/en) is used to manage the testing of e2nest.

```tox```: run unit tests, browser tests and style check.

```tox -e unittest```: run all unit tests only

```tox -e browser```: run all browser tests only (see [Browser tests based on Selenium](#browser-tests-based-on-selenium))

```tox -e style```: run style check only

To run a specific test:

```DJANGO_SETTINGS_MODULE=nest_site.settings python manage.py test -v 2 nest.tests.<test file>.<test class>.<test name>```

For example:

```DJANGO_SETTINGS_MODULE=nest_site.settings python manage.py test -v 2 nest.tests.nest_view_tests.TestViewsWithWriteDataset.test_step_session```

## Set up project in PyCharm

To set up project in PyCharm, in Preferences > Project > Python Interpreter, set the Python interpreter to `.venv/bin/python`. Then, in the Project panel on the left, browse to folder `e2nest/nest_site`, right-click, Mark Directory as > Source Root. (Note that if you still see paths marked as red in your code, restart PyCharm may solve the problem.)

## Browser tests based on Selenium

The testing of web page elements including HTML/CSS/Javascript can be enabled by setting up the [Selenium](https://www.selenium.dev/) framework. More tutorial on this can be found in Django's [LiveServerTestCase](https://docs.djangoproject.com/en/4.0/topics/testing/tools/#django.test.LiveServerTestCase) page. Below are the setup steps:
- Download [chromedriver](https://chromedriver.chromium.org/home). Put the executable at a local directory, such as `/var/chromedriver`.
- Add `CHROMEDRIVER_PATH = '/var/chromedriver'` line to `nest_site/settings.py`.
- The browser tests can be invoked by:
```shell
DJANGO_SETTINGS_MODULE=nest_site.settings python manage.py test -v 2 nest.tests.nest_browsertests
```
or simply
```shell
tox -e browser
```

## Run server

Before running server, first create a super-user:
```
python manage.py createsuperuser
```
Note that the above command is for creating a superuser with admin permissions. For creating username/password for test subjects, please see [User command line tools](#user-command-line-tools) section.

Run server locally by:
```
python manage.py runserver 8000
```
