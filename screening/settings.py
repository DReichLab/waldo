"""
Django settings for screening project.

Generated by 'django-admin startproject' using Django 1.8.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from .secret_settings import *

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['localhost', 'screening.reichdna.hms.harvard.edu', 'testing.reichdna.hms.harvard.edu']


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'sequencing_run',
)

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'screening.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'screening.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'US/Eastern'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

# O2 specific settings
PIPELINE_USERS = ['mym11', 'adm515']
COMMAND_HOST = "o2.hms.harvard.edu"
TRANSFER_HOST = "transfer.rc.hms.harvard.edu"
FILES_SERVER_DIRECTORY = "/files/Genetics/reichseq/reich/reichseq/reich"
SCRATCH_PARENT_DIRECTORY = "/n/scratch3/users/m/mym11/automated_pipeline"

GROUPS_DIRECTORY = "/n/groups/reich/matt/pipeline/"
RUN_FILES_DIRECTORY = os.path.join(GROUPS_DIRECTORY, 'run')
RUN_RELEASE_FILES_DIRECTORY = os.path.join(RUN_FILES_DIRECTORY, 'release')
RESULTS_PARENT_DIRECTORY = os.path.join(GROUPS_DIRECTORY, 'results')

RELEASED_LIBRARIES_DIRECTORY = os.path.join(GROUPS_DIRECTORY, 'released_libraries')
CONTROL_LIBRARIES_DIRECTORY = os.path.join(GROUPS_DIRECTORY, 'controls')
CONTROL_ID = 'Contl.Capture'
CONTROL_PCR_ID = 'Contl.PCR'

DEMULTIPLEXED_PARENT_DIRECTORY = "/n/groups/reich/matt/pipeline/demultiplex"
DEMULTIPLEXED_BROAD_SHOTGUN_PARENT_DIRECTORY = '/n/data1/hms/genetics/reich/1000Genomes/lh3/hominid/demultiplex'
NUCLEAR_SUBDIRECTORY = "nuclear_aligned_filtered"
MT_SUBDIRECTORY = "rsrs_aligned_filtered"

HUMAN_REFERENCE='human_g1k_v37.fasta'
SHOTGUN_HUMAN_REFERENCE='hs37d5.fa'
