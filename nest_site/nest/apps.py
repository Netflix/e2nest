from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig


class NestConfig(AppConfig):
    name = 'nest'
    default_site = 'nest.sites.NestSite'


class NestAdminConfig(AdminConfig):
    default_site = 'nest.sites.NestAdminSite'
