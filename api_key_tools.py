"""This module creates an API Key Class object to provide various tools regarding
build of API Key files

Exported Classes
ApiKeyTools
"""
import os


class ApiKeyTools:
    """
    A class used to create an OciConsumer object

    Parameters
    ----------
    config: instance
       Configuration values in ConfigParser object

    Attributes
    ----------
    config: instance
        Instance of ConfigParser object

    Methods
    -------
    build_key_files()
        Dynamically builds PEM key files for OCI authentication
    _create_folder(path)
        Creates a specified folder if it doesn't exist
    """

    def __init__(self, config):
        self.config = config

    def build_key_files(self):
        """Dynamically builds PEM key files for OCI authentication"""
        key_files = [
            {
                'file_path': '/apikeys',
                'file_name': 'oci_svc_user_key_public.pem',
                'config_key': 'oci_svc_user_public_key'
            },
            {
                'file_path': '/apikeys',
                'file_name': 'oci_svc_user_key.pem',
                'config_key': 'oci_svc_user_private_key'
            }
        ]

        for key_file in key_files:
            self._create_folder(path=key_file['file_path'])

            key_file_path = '{0}/{1}'.format(key_file['file_path'], key_file['file_name'])
            with open(key_file_path, 'w') as f:
                file_lines = str(self.config.get('oci', key_file['config_key'])).split(',')

                for line in file_lines:
                    f.write(str(line) + '\n')

            print('Key file {0} created.'.format(key_file_path))

    @staticmethod
    def _create_folder(path):
        """Creates a specified folder if it doesn't exist"""
        does_exist = os.path.exists(path)

        if not does_exist:
            os.makedirs(path)
