"""This module creates an OCI Consumer Class object to provide various OCI Stream
functionality for the application

Exported Classes
OciConsumerTools
"""
import os
import oci
from datetime import datetime
import json
from base64 import b64decode

from file_management import CreateCsvFile
from config import get_config


class OciConsumerTools:
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
    data_dict: dict
        Dictionary to hold all the messages of the stream
    oci_stream_client: instance
        Instance of OCI Stream Client
    group_cursor: instance
        Instance of OCI Cursor

    Methods
    -------
    consume_messages()
        Consumes list of OCI message objects from OCI Stream
    _get_oci_configuration()
        Returns configuration dictionary for OCI authentication
    _validate_config(oci_config)
        Validates OCI configuration
    _get_oci_stream_client(oci_config)
        Returns OCI Streaming Client for interacting with OCI stream
    _get_message_key()
        Returns string with timestamp for message key
    _get_cursor_by_group
        Creates cursor for temporary stream message storage
    _update_group_response()
        Manually updates the cursor if partitions has fallen behind the trim horizon
    _message_loop()
        Processes the cursor message list
    _process_messages()
        Reads a stream of predetermined amount of messages and returns them as a list
    _process_message_list()
        Loops through the message list, creates a local json file for each, then converts file to csv and upload to S3
    _create_folder()
        Creates a 'tmp' folder to temporarily hold json and csv files
    _create_json()
        Creates a local Json file of the list of messages
    """

    def __init__(self, config):
        self.config = config
        self.data_dict = dict()
        self.folder_name = self.config.get('app', 'data_directory')

        oci_config = self._get_oci_configuration()
        self._validate_config(oci_config=oci_config)
        self.oci_stream_client = self._get_oci_stream_client(oci_config=oci_config)
        self.group_cursor = self._get_cursor_by_group(self.oci_stream_client, self.config.get('oci', 'oci_stream_ocid'))

    def _get_oci_configuration(self):
        """Returns configuration dictionary for OCI authentication"""

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

    def _get_oci_stream_client(self, oci_config):
        """Returns OCI Stream Client for interacting with OCI stream"""

        try:
            stream_client = oci.streaming.StreamClient(oci_config,
                                                       service_endpoint=self.config.get('oci', 'oci_message_endpoint'))
            print('OCI stream client ({0}) created'.format(stream_client))
        except Exception as e:
            print('_get_oci_stream_client', e)
        else:
            return stream_client

    def _get_message_key(self):
        """Returns string with timestamp for message key"""

        key_base = self.config.get('oci', 'key_base')
        timestamp = str(datetime.now())

        message_key = '{0}{1}'.format(key_base, timestamp)

        return message_key

    @staticmethod
    def _get_cursor_by_group(sc, sid, group_name='analyplat_consumer', instance_name='apprise_consumer'):
        """Creates a group cursor to consume messages from stream"""

        print("\nCreating a cursor for group {}, instance {}".format(group_name, instance_name))
        cursor_details = oci.streaming.models.CreateGroupCursorDetails(group_name=group_name,
                                                                       instance_name=instance_name,
                                                                       type=oci.streaming.models.CreateGroupCursorDetails.TYPE_TRIM_HORIZON,
                                                                       commit_on_get=True)

        response = sc.create_group_cursor(sid, cursor_details)
        return response.data.value

    @staticmethod
    def _update_group_response(sc, sid, group_name='analyplat_consumer'):
        """Updates the group cursor if 'invalid' error received from stream"""

        sc.update_group(stream_id=sid, group_name=group_name,
                        update_group_details=oci.streaming.models.UpdateGroupDetails(
                            type="AT_TIME",
                            time=datetime.now()),
                        opc_request_id="MXPAHQCSFRQG7N8NCUJB<unique_ID>")

    def _message_loop(self, client, stream_id, initial_cursor, config):
        """Launches loop to consume messages from stream"""

        message_cursor = initial_cursor

        while True:
            get_response = client.get_messages(stream_id, message_cursor, limit=500)
            # No messages to process then return
            if not get_response.data:
                print('Finish looping through all the batches\n')
                return

            new_message_list = self._process_messages(get_response)

            self._process_message_list(new_message_list, config)

            # Move to the next-cursor to continue consuming
            print('\nPreparing cursor to consume next batch of messages')
            message_cursor = get_response.headers["opc-next-cursor"]

    def _process_messages(self, get_response):
        """Creates a list of messages from cursor to further process"""

        print("Read a batch including {} messages".format(len(get_response.data)))
        new_message_list = list()
        for message in get_response.data:
            # Decode message stream
            if message.key:
                key = b64decode(message.key.encode()).decode() + "-CONSUMED@" + str(datetime.today()) + \
                      "-OFFSET@" + str(message.offset)
            else:
                print('Empty Key')
                key = str(datetime.today()) + 'Empty Key'
            value = b64decode(message.value.encode()).decode(errors='ignore')
            self.data_dict[key] = value
            new_message_list.append({key: value})

        return new_message_list

    def _process_message_list(self, new_message_list, config):
        """Takes individual message from list, creates local json, flattens, creates local csv and uploads to S3"""

        # loop though message list to create a list of dictionaries containing messages
        if len(new_message_list) >= 1:
            self._create_folder()
            today_date = datetime.today().strftime('%m%d%Y%H%M%S')
            json_file_name = '{}/apprise_{}.json'.format(self.folder_name, today_date)
            self._create_json(json_file_name, new_message_list)
            # Create csv file and upload to S3
            csv = CreateCsvFile(json_file_name, config=config)
            csv.create_csv(self.folder_name)

    def _create_folder(self):
        """Creates a specified folder if it doesn't exist"""

        does_exist = os.path.exists(self.folder_name)

        if not does_exist:
            os.makedirs(self.folder_name)

    @staticmethod
    def _create_json(json_file_name, new_message_list):
        """Creates a local json file"""

        try:
            print('Creating Json file ...')
            json.dump(new_message_list, open(json_file_name, "w"))
        except Exception as e:
            print('Problem creating json file', e)

    def consume_messages(self):
        """Launches the stream consumer, updates group cursor if invalid"""

        try:
            self._message_loop(self.oci_stream_client, self.config.get('oci', 'oci_stream_ocid'),
                               self.group_cursor, self.config)
        except oci.exceptions.RequestException:
            self._update_group_response(self.oci_stream_client, self.config.get('oci', 'oci_stream_ocid'))
            self._message_loop(self.oci_stream_client, self.config.get('oci', 'oci_stream_ocid'),
                               self.group_cursor, self.config)
        except Exception as e:
            print('Problem with the OCI stream', e)
        else:
            print('End of message consumption')
