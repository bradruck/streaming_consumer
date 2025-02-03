""""This module orchestrates the running of the application. The purpose of the application:
1) Generate key files to be used for authenticating the OCI stream client
2) Consume messages from OCI stream for use in reporting analytics
3) Create and upload csv file of stream messages to Datalake (OS location)
"""
import datetime
import os

from api_key_tools import ApiKeyTools
from oci_consumer_tools import OciConsumerTools
from config import get_config

os.environ["NLS_LANG"] = ".AL32UTF8"

print('Application run time START: {0}\n'.format(datetime.datetime.now()))

print('Getting application config...')
config = get_config()

print('Building key files...')
api_key_tools = ApiKeyTools(config=config)
api_key_tools.build_key_files()

print('Consuming message(s) from OCI Stream...')
oci_consumer = OciConsumerTools(config=config)
oci_consumer.consume_messages()

print('\nApplication run time END: {0}'.format(datetime.datetime.now()))
