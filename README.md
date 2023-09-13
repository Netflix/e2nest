# e2nest - Web-based Media Subjective Testing Platform

## Virtual environment setup

```shell
python3 -m virtualenv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

(```deactivate```: exit the virtual environment)

For all instructions below, assume you have `cd` into `./nest_site`.

## Provide secret key and host address

You need to replace `"PUT_YOUR_SECRET_KEY_HERE"` with your own [secret key](https://docs.djangoproject.com/en/2.2/ref/settings/#secret-key). The secret key is used mostly to provide cryptographic signing for session cookies. This can be any string of your choice, but the longer and more random the better.

If you are hosting your server on a remote host (for example, an AWS EC2 instance) instead of your own computer as a localhost, you need to replace `"PUT_YOUR_SERVER_IP_HERE"` with the remote host's public IP address.

## Database setup

Currently, sqlite3 is being configured as the database type.

```python manage.py makemigrations```: create database migration files under migrations/.

```python manage.py migrate```: The migrate command looks at the INSTALLED_APPS setting and creates any necessary database tables according to the migration files.

## Run tests in terminal

To run a specific test (verbosely):

```DJANGO_SETTINGS_MODULE=nest_site.settings python manage.py test -v 2 nest.tests.<test file>.<test class>.<test name>```

For example:

```DJANGO_SETTINGS_MODULE=nest_site.settings python manage.py test -v 2 nest.tests.nest_view_tests.TestViewsWithWriteDataset.test_step_session```

## Set up project in PyCharm

To set up project in PyCharm, in Preferences > Project > Python Interpreter, set the Python interpreter to `.venv/bin/python`. Then, in the Project panel on the left, browse to folder `e2nest/nest_site`, right-click, Mark Directory as > Source Root. (Note that if you still see paths marked as red in your code, restart PyCharm may solve the problem.)
