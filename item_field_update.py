import configparser
import datetime
import logging
import os
import sys

from py_jama_rest_client.client import JamaClient

logger = logging.getLogger(__name__)


def init_logging():
    try:
        os.makedirs('logs')
    except FileExistsError:
        pass
    current_date_time = datetime.datetime.now().strftime("%Y-%m-%d %H_%M_%S")
    log_file = 'logs/dox_importer_' + str(current_date_time) + '.log'
    logging.basicConfig(filename=log_file, level=logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


def parse_config():
    # allow the user to shorthand this and just look for the 'config.ini' file
    if len(sys.argv) == 1:
        current_dir = os.path.dirname(__file__)
        path_to_config = 'config.ini'
        if not os.path.isabs(path_to_config):
            path_to_config = os.path.join(current_dir, path_to_config)

    # use the config file location
    if len(sys.argv) == 2:
        current_dir = os.path.dirname(__file__)
        path_to_config = sys.argv[1]
        if not os.path.isabs(path_to_config):
            path_to_config = os.path.join(current_dir, path_to_config)

    # Parse config file.
    configuration = configparser.ConfigParser()
    try:
        with open(path_to_config, encoding="utf8", errors='ignore') as file:
            configuration.read_file(file)
    except Exception as e:
        logger.error("Unable to parse configuration file. exception: " + str(e))
        exit(1)

    return configuration


def create_jama_client(config: configparser.ConfigParser):
    global instance_url
    url = None
    user_id = None
    user_secret = None
    oauth = None
    try:
        url = config.get('CLIENT_SETTINGS', 'jama_connect_url').strip()
        # Clenup URL field
        while url.endswith('/') and url != 'https://' and url != 'http://':
            url = url[0:len(url) - 1]
        # If http or https method not specified in the url then add it now.
        if not (url.startswith('https://') or url.startswith('http://')):
            url = 'https://' + url
        oauth = config.getboolean('CLIENT_SETTINGS', 'oauth')
        user_id = config.get('CLIENT_SETTINGS', 'user_id').strip()
        user_secret = config.get('CLIENT_SETTINGS', 'user_secret').strip()
        instance_url = url
    except configparser.Error as config_error:
        logger.error("Unable to parse CLIENT_SETTINGS from config file because: {}, "
                     "Please check config file for errors and try again."
                     .format(str(config_error)))
        exit(1)

    return JamaClient(url, (user_id, user_secret), oauth=oauth)


if __name__ == "__main__":
    # Setup logging
    init_logging()

    # Get Config File Path
    conf = parse_config()

    # Create Jama Client
    jama_client = create_jama_client(conf)

    # get the required script parameters
    filter_id = 97
    item_type = 142
    read_field = 'doors_id'
    write_field = 'sys_doors_id'
    try:
        filter_id = conf.getint('SCRIPT_SETTINGS', 'filter_id')
        item_type = conf.getint('SCRIPT_SETTINGS', 'item_type')
        read_field = conf.get('SCRIPT_SETTINGS', 'read_field').strip()
        write_field = conf.get('SCRIPT_SETTINGS', 'write_field').strip()
    except Exception as e:
        logger.error(
            'Failed to retrieve required script params, please confirm config file. exception: {}'.format(str(e)))
        sys.exit(1)

    # run some validations on the script parameters
    item_type_name = ''
    fields = []
    try:
        item_type_definition = jama_client.get_item_type(item_type)
        item_type_name = item_type_definition.get('name')
        fields = item_type_definition.get('fields')

    except Exception as e:
        logger.error('Invalid script params, please confirm config file. exception: {}'.format(str(e)))
        sys.exit(1)

    read_field_found = False
    write_field_found = False
    for field in fields:
        if field['name'].startswith(read_field):
            read_field_found = True
            read_field = field['name']
        if field['name'].startswith(write_field):
            write_field_found = True
            write_field = field['name']
        if read_field_found and write_field_found:
            break

    if not read_field_found:
        logger.error('unable to locate read_field: {} on item type: {}'.format(read_field, item_type_name))
        sys.exit(1)
    if not write_field_found:
        logger.error('unable to locate write_field: {} on item type: {}'.format(write_field, item_type_name))
        sys.exit(1)

    # do the work
    filter_items = []
    logger.info('Retrieving filter items from filter ID:{} ...'.format(filter_id))
    try:
        filter_items = jama_client.get_filter_results(filter_id)
    except Exception as e:
        logger.error('Unable to retrieve filter items exception: {}'.format(str(e)))
        sys.exit(1)
    logger.info('Successfully retrieved {} filter items'.format(len(filter_items)))

    logger.info('processing filter items...')
    update_item_list = []
    for filter_item in filter_items:
        # only process items that match the correct item type
        if 'itemType' in filter_item and filter_item['itemType'] == item_type:
            # check to see if there is work that needs to be done on this item
            item_fields = filter_item['fields']
            # we must have a read field here to do work
            if read_field in item_fields and item_fields[read_field] != '':
                # empty write field? def needs updating here
                if write_field not in item_fields:
                    update_item_list.append(filter_item)
                # different matching values here? another update here
                elif item_fields[write_field] != item_fields[read_field]:
                    update_item_list.append(filter_item)

    logger.info('Identified {} items to be updated'.format(len(update_item_list)))

    counter = 1
    for update_item in update_item_list:
        write_value = update_item['fields'][read_field]
        logger.info(
            'Updating item {}/{}     ID:{} field:{} update-value:{} ...'.format(counter, len(update_item_list), update_item['id'],
                                                                      write_field, write_value))


        patch = [{
                    "op": 'add' if write_field_found else 'replace',
                    "path": '/fields/{}'.format(write_field),
                    "value": write_value
                }]

        try:
            response = jama_client.patch_item(update_item['id'], patch)
            if response == 'OK':
                logger.info('Successfully updated item')
        except Exception as e:
            logger.error('FAILED to update item exception: {}'.format(str(e)))
        counter += 1

    logger.info('done')
