"""This module creates an AWS S3 Tools Class object to provide various S3
functionality for the application

Exported Classes
S3Tools
"""

import boto3
import json
import os

from config import get_config


class S3Tools:
    """
    A class used to create an S3Tools object

    Parameters
    ----------
    config: instance
       Configuration values in ConfigParser object

    Attributes
    ----------
    config: instance
        Instance of ConfigParser object
    s3_resource: instance
        Instance of AWS S3 Resource object
    s3_client: instance
        Instance of AWS S3 Client object

    Methods
    -------
    get_current_data_files()
        Downloads all new data files
    _create_folder(path)
        Creates a specified folder if it doesn't exist
    _get_file_list(s3_bucket, s3_prefix)
        Returns list of new files for processing from specific AWS location
    _update_published_file_log(filtered_file_list)
        Updates list of files that have been published in the log file
    _create_s3_session()
        Returns AWS S3 Session object
    _create_s3_resource()
        Returns AWS S3 Resource object
    _create_s3_client()
        Returns AWS S3 Client object
    _get_filter_list()
        Returns a list of files that have previously been published
    _filter_previously_published_files(full_list)
        Returns list of path/filenames of files that haven't previously been uploaded
    _download_file(s3_bucket, s3_prefix, local_directory, file_name)
        Downloads S3 file to local location
    _upload_file(s3_bucket, s3_prefix, local_directory, file_name
        Uploads local file to S3 location
    _delete_file(s3_bucket, s3_prefix, file_name)
        Deletes file in S3 location
    """

    def __init__(self, config):
        self.config = config
        self.s3_session = self._create_s3_session()
        self.s3_resource = self._create_s3_resource()
        self.s3_client = self._create_s3_client()

    def get_current_data_files(self):
        """Downloads all new data files"""
        self._create_folder(path=self.config.get('app', 'data_directory'))

        filtered_file_list = self._get_file_list(s3_bucket=self.config.get('s3', 's3_bucket'),
                                                 s3_prefix=self.config.get('s3', 's3_prefix'))

        for file_name in filtered_file_list:
            self._download_file(s3_bucket=self.config.get('s3', 's3_bucket'),
                                s3_prefix=self.config.get('s3', 's3_prefix'),
                                local_directory=self.config.get('app', 'data_directory'),
                                file_name=file_name)

        self._update_published_file_log(filtered_file_list=filtered_file_list)

        print('{0} data files downloaded from S3'.format(len(filtered_file_list)))

    def upload_csv_file(self, file_name):
        """Uploads local csv file to S3 location"""
        self._upload_file(self.config.get('s3', 's3_bucket'), self.config.get('s3', 's3_prefix'), 'tmp', file_name)

    @staticmethod
    def _create_folder(path):
        """Creates a specified folder if it doesn't exist"""
        does_exist = os.path.exists(path)

        if not does_exist:
            os.makedirs(path)

    def _get_file_list(self, s3_bucket, s3_prefix):
        """Returns list of new files for processing from specific AWS location"""
        full_list = []
        filtered_list = []

        try:
            s3_response = self.s3_client.list_objects_v2(Bucket=s3_bucket, Prefix=s3_prefix)

            file_objects = s3_response.get("Contents")
            for file_object in file_objects:
                file_path_list = file_object['Key'].split('/')
                filename = file_path_list[-1]
                if filename:
                    full_list.append(filename)

            filtered_list = self._filter_previously_published_files(full_list=full_list)
        except Exception as e:
            print('get_file_list => ', e)

        return filtered_list

    def _update_published_file_log(self, filtered_file_list):
        """Updates list of files that have been published in the log file"""

        target_file_path = self.config.get('app', 'data_directory')
        target_file_name = self.config.get('s3', 'published_file_log_name')
        target_file = '{0}/{1}'.format(target_file_path, target_file_name)
        target_key = self.config.get('s3', 'logfile_key')

        filter_list = self._get_filter_list()

        for file_name in filtered_file_list:
            filter_list.append(file_name)

        log_file_dict = {target_key: filter_list}

        with open(target_file, 'w') as f:
            json.dump(log_file_dict, f)

        # Uncomment below when desiring to begin uploading the "previously published" list
        # self._upload_file(s3_bucket=self.config.get('s3', 's3_bucket'),
        #                   s3_prefix=self.config.get('s3', 's3_prefix'),
        #                   local_directory=self.config.get('app', 'data_directory'),
        #                   file_name=self.config.get('s3', 'published_file_log_name'))

    def _create_s3_session(self):
        """Returns AWS S3 Session object"""
        s3_session = boto3.Session(
            aws_access_key_id=self.config.get('s3', 'aws_access_key'),
            aws_secret_access_key=self.config.get('s3', 'aws_secret'),
        )

        print('s3_session object ({0}) created'.format(s3_session))

        return s3_session

    def _create_s3_resource(self):
        """Returns AWS S3 Resource object"""
        s3_session = self._create_s3_session()
        s3_resource = s3_session.resource('s3')

        print('s3_resource object ({0}) created'.format(s3_resource))

        return s3_resource

    def _create_s3_client(self):
        """Returns AWS S3 Client object"""
        s3_client = boto3.client(
            's3',
            aws_access_key_id=self.config.get('s3', 'aws_access_key'),
            aws_secret_access_key=self.config.get('s3', 'aws_secret')
        )

        print('s3_client object ({0}) created'.format(s3_client))

        return s3_client

    def _get_filter_list(self):
        """Returns a list of files that have previously been published"""
        target_file_path = '{0}/{1}'.format(self.config.get('app', 'data_directory'),
                                            self.config.get('s3', 'published_file_log_name'))
        target_key = self.config.get('s3', 'logfile_key')

        with open(target_file_path, 'r') as f:
            data = json.load(f)
            filter_list = data[target_key]

        return filter_list

    def _filter_previously_published_files(self, full_list):
        """Returns list of path/filenames of files that haven't previously been uploaded"""
        filtered_list = []

        self._download_file(s3_bucket=self.config.get('s3', 's3_bucket'),
                            s3_prefix=self.config.get('s3', 's3_prefix'),
                            local_directory=self.config.get('app', 'data_directory'),
                            file_name=self.config.get('s3', 'published_file_log_name'))
        filter_list = self._get_filter_list()

        for file_name in full_list:
            if file_name not in filter_list:
                filtered_list.append(file_name)

        return filtered_list

    def _download_file(self, s3_bucket, s3_prefix, local_directory, file_name):
        """Downloads S3 file to local location"""

        source_object = '{0}/{1}'.format(s3_prefix, file_name)
        target_object = '{0}/{1}'.format(local_directory, file_name)
        try:
            self.s3_resource.Bucket(s3_bucket).download_file(source_object, target_object)
        except Exception as e:
            print('_download_file => ', e)

    def _upload_file(self, s3_bucket, s3_prefix, local_directory, file_name):
        """Uploads local file to S3 location"""

        target_object = '{0}/{1}'.format(s3_prefix, file_name)
        source_object = '{0}/{1}'.format(local_directory, file_name)
        try:
            self.s3_client.upload_file(source_object, s3_bucket, target_object)
        except Exception as e:
            print('_upload_file => ', e)

    def _delete_file(self, s3_bucket, s3_prefix, file_name):
        """Deletes file in S3 location"""
        target_object = '{0}/{1}'.format(s3_prefix, file_name)

        try:
            self.s3_client.delete_object(Bucket=s3_bucket, Key=target_object)
        except Exception as e:
            print('_delete_file', e)
