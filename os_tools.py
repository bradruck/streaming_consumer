"""This module creates an OS Tools Class object to provide various OS
functionality for the application

Exported Classes
OSTools
"""

import oci.object_storage
import json
import os
import io

from config import get_config


class OSTools:
    """
    A class used to create an OSTools object

    Parameters
    ----------
    config: instance
       Configuration values in ConfigParser object

    Attributes
    ----------
    config: instance
        Instance of ConfigParser object
    oci_os_client: instance
        Instance of OS Client object

    Methods
    -------
    _get_oci_configuration()
        Returns configuration dictionary
    _validate_config()
        Validates OS configuration
    __get_oci_os_client()
        Returns OS Client object
    upload_csv_file(file_name)
        Uploads local csv file to OS location
    upload_json_file(file_name)
        Uploads local csv file to OS location
    _put_os_object(os_namespace, os_bucket, file_name, os_prefix, local_directory)
        Uploads local file to OS location
    _delete_os_object(os_namespace, os_bucket, os_prefix, file_name, os_prefix)
        Deletes file in OS location
    """

    def __init__(self, config):
        self.config = config
        self.data_dict = dict()
        self.folder_name = self.config.get('app', 'data_directory')

        oci_config = self._get_oci_configuration()
        self._validate_config(oci_config=oci_config)
        self.oci_os_client = self._get_oci_os_client(oci_config=oci_config)

    def _get_oci_configuration(self):
        """Returns configuration dictionary for OS authentication"""

        oci_config = {
            "user": self.config.get('oci', 'oci_svc_user_ocid'),
            "fingerprint": self.config.get('oci', 'oci_svc_user_fingerprint'),
            "key_file": self.config.get('oci', 'key_file'),
            "tenancy": self.config.get('oci', 'tenancy'),
            "region": self.config.get('oci', 'region')
        }

        return oci_config

    @staticmethod
    def _validate_config(oci_config):
        """Validates OCI configuration"""

        try:
            oci.config.validate_config(oci_config)
            print('OCI configuration validated')
        except Exception as e:
            print('_validate_config', e)

    def _get_oci_os_client(self, oci_config):
        """Returns OCI OS Client for interacting with OCI Object Storage"""

        try:
            os_client = oci.object_storage.ObjectStorageClient(oci_config)
            print('OCI os client ({0}) created'.format(os_client))
            print('Working in namespace: {}, compartment: {}'.format(os_client.get_namespace().data, self.config.get('os', 'os_compartment')))
        except Exception as e:
            print('_get_oci_os_client', e)
        else:
            return os_client

    def upload_csv_file(self, object_name):
        """Uploads local csv file to S3 location"""
        self._put_os_object(self.config.get('os', 'os_namespace'), self.config.get('os', 'os_bucket'), object_name, self.config.get('os', 'os_prefix_csv'), self.config.get('app', 'data_directory'))

    def upload_json_file(self, object_name):
        """Uploads local json file to S3 location"""
        self._put_os_object(self.config.get('os', 'os_namespace'), self.config.get('os', 'os_bucket'), object_name, self.config.get('os', 'os_prefix_json'), self.config.get('app', 'data_directory'))

    def _put_os_object(self, namespace, bucket, object_name, os_directory, local_directory):
        """Uploads local file to OS location"""

        try:
            print('Uploading {} to object storage location {}...'.format(object_name, os_directory))
            with open(os.path.join(local_directory, object_name), 'rb') as in_file:
                self.oci_os_client.put_object(namespace, bucket, os.path.join(os_directory, object_name), in_file)
        except Exception as e:
            print('_put_os_object', e)
        else:
            print('Success, file {} uploaded to object storage'.format(os.path.join(os_directory, object_name)))

    def _delete_os_object(self, namespace, bucket, object_name, os_directory):
        """Deletes file from OS location"""

        try:
            self.oci_os_client.delete_object(namespace, bucket, os.path.join(os_directory, object_name))
        except Exception as e:
            print('_delete_os_object', e)
        else:
            print('Success, file {} deleted from object storage'.format(os.path.join(os_directory, object_name)))
