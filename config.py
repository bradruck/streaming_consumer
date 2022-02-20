"""This module creates orchestrates the creation of a config object to be
used in the application. It source values from the config.ini file and environment
variables provided through the secure Vault application and Kubernetes
"""

import configparser
import os


def _add_ini_config():
    """Returns the base config object from values in the config.ini file"""
    config = configparser.ConfigParser()
    config.read('config.ini')

    return config


def _add_env_config(config):
    """Adds additional values to the config object that have been stored in the environment"""
    config.set('s3', 'aws_access_key', os.environ['AWS_ACCESS_KEY'])
    config.set('s3', 'aws_secret', os.environ['AWS_SECRET'])

    config.set('oci', 'oci_stream_ocid', os.environ['OCI_STREAM_OCID'])
    config.set('oci', 'oci_svc_user_ocid', os.environ['OCI_SVC_USER_OCID'])
    config.set('oci', 'oci_svc_user_fingerprint', os.environ['OCI_SVC_USER_FINGERPRINT'])
    config.set('oci', 'oci_svc_user_public_key', os.environ['OCI_SVC_USER_PUBLIC_KEY'])
    config.set('oci', 'oci_svc_user_private_key', os.environ['OCI_SVC_USER_PRIVATE_KEY'])

    return config


def get_config():
    """Returns the complete config application with all necessary values for the application"""
    config = _add_ini_config()
    config = _add_env_config(config=config)

    return config
