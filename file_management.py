import os
import json
from datetime import datetime
from csv import DictWriter
import flatdict
from ast import literal_eval
#from s3_tools import S3Tools
from os_tools import OSTools


class CreateCsvFile:
    """
    A class used to create an OciConsumer object

    Parameters
    ----------
    config: instance
        Configuration values in ConfigParser object
    json_file_name: basestring
        Local Json file name

    Attributes
    ----------
    config: instance
        Instance of ConfigParser object
    today_date: basestring
        String representation of today's date
    csv_file_name: basestring
        Csv file name
    json_file_name: basestring
        Json file name

    Methods
    -------
    create_csv()
        Unpacks a Json file, flattens the structure and loads the data into a csv file, then uploads to S3 location
        and deletes the Json file
    _flatten_file(path)
        Loads the Json file contents into a dictionary structure, then removes layers for a flat structure
    _find_column_headers
        Searches all the messages and searches for one with the most attributes, creating a csv header list
    """

    def __init__(self, json_file_name, config):
        self.config = config
        self.today_date = datetime.today().strftime('%m%d%Y%H%M%S')
        self.csv_file_name = 'apprise_{}.csv'.format(self.today_date)
        self.json_file_name = json_file_name

    def _flatten_json(self):
        """Creates a flattened dictionary from Json file"""

        try:
            with open(self.json_file_name, 'r') as file:
                json_objects = json.load(file)
        except Exception as e:
            print('Problem opening json file', e)
        else:
            # convert the json objects to dicts and flatten
            flat_data = list()
            for obj in json_objects:
                for k, v in obj.items():
                    # find the stream offset that is part of the key
                    offset = k.split('@')[-1]
                    # replace stream values with valid python values
                    v = v.replace('false', 'False')
                    v = v.replace('true', 'True')
                    v = v.replace('null', '')
                    # convert string-dict to dictionary
                    v = literal_eval(v)
                    # convert nested dictionary to flattened dictionary
                    flat_dict = flatdict.FlatterDict(v)
                    # modify nested-key values
                    flat_dict = {k.replace(':', '_'): v[0] for k, v[0] in flat_dict.items()}
                    flat_dict = {k.replace('-', '_'): v[0] for k, v[0] in flat_dict.items()}
                    flat_dict = {k.replace('–', '_'): v[0] for k, v[0] in flat_dict.items()}
                    flat_dict = {k.replace('—', '_'): v[0] for k, v[0] in flat_dict.items()}
                    # add the offset key:value pair to the message dict
                    flat_dict['oci_stream_offset'] = offset
                    flat_data.append(flat_dict)
            return flat_data

    @staticmethod
    def _find_column_headers(flattest_data):
        """Searches all the messages and creates a csv heading list from all included columns"""

        latest_list = list(flattest_data[0].keys())
        for event in flattest_data:
            for item in event:
                if item not in latest_list:
                    latest_list.append(item)
        return latest_list

    def create_csv(self, folder_path):
        """Creates a local csv file from the flattened dict, then uploads to OS location, deletes local Json and csv"""
        #s3_upload = S3Tools(self.config)
        os_upload = OSTools(self.config)

        # commented out when not required
        '''try:
            print('Uploading json file to S3 ....')
            s3_upload.upload_json_file(self.json_file_name.split('/')[-1])
        except Exception as e:
            print('Problem uploading json file', e)'''

        print('Flattening Json ....')
        flattened_data = self._flatten_json()
        print('Creating csv file ....')
        csv_columns = self._find_column_headers(flattened_data)

        try:
            with open('{}/{}'.format(folder_path, self.csv_file_name), 'w') as csv_file:
                writer = DictWriter(csv_file, fieldnames=csv_columns)
                writer.writeheader()
                writer.writerows(flattened_data)
        except Exception as e:
            print('Problem creating csv file', e)
        else:
            #print('Uploading csv file to S3 ....')
            print('Uploading csv file to OS ....')
            #s3_upload.upload_csv_file(self.csv_file_name)
            os_upload.upload_csv_file(self.csv_file_name)
            # Delete local Json file
            os.remove(self.json_file_name)
            # Delete local Csv file
            os.remove('{}/{}'.format(folder_path, self.csv_file_name))
