# Item Field Update
The purpose of this script is to update fields from a list of items.

- This list of items is specified by the API ID of a public filter
- Each item being updated must have a source field and target field to copy the data over to

## Installation
This section contains information on how to install the required dependencies for this script.

### Pre-Requisites
* [Python 3.7+](https://www.python.org/downloads/release/python-377/) If using pipenv you must use a python 3.7.X 
version.  If installing requirements manually you may use any python version including 3.8+ however testing has only
been done against python 3.7

* [py-jama-rest-client](https://pypi.org/project/py-jama-rest-client/)

* Enable the REST API on your Jama Connect instance

## Pipenv installation (Recommended)
If you do not already have Pipenv installed on your machine you can learn how to install it here: 
[https://pypi.org/project/pipenv/](https://pypi.org/project/pipenv/)

The required dependencies for this project are managed with Pipenv and can be installed by opening a terminal
to the project directory and entering the following command:
```bash
pipenv install
```

## Manual installation
If you do not wish to use Pipenv you may manually install the required dependencies with pip.
```bash
pip install --user py-jama-rest-client
```

## Usage
This section contains information on configuration and execution the script.

### Configuration
Before you can execute the script you must configure the script via a config file.  The config file is
structured in a standard .ini file format. there is an example config.ini file included with this repo that you
may modify with your settings.  I recommend that you create a copy of the template config file and rename it to
something that is meaningful for your execution.

#### Client Settings:
This section contains settings related to connecting to your Jama Connect REST API.

* `jama_connect_url`: this is the URL to your Jama Connect instance

* `oauth`: setting this value to 'false' will instruct the client to authenticate via basic authentication.  Setting this 
value to 'true' instructs the client to use OAuth authentication protocols

* `user_id`: This should be either your username or clientID if using OAuth

* `user_secret`: This should be either your password or client_secret if using OAuth

#### Script Settings:
This section contains settings required to run the script
* `filter_id`: API ID of the public filter (number)
* `item_type`: API ID of the item type to be processed (number)
* `read_field`: API field name of the source field (string)
* `write_field`: API field name of the target field (string)


You can get the filter API ID by first navigating to it in Jama then grabbing it from the url its the number 
right after "filters/". 

The API item type ID and api names can be found in Jama from the admin tab > item types


## Running the script

1) Open a terminal to the project directory.
2) If using pipenv enter the following(otherwise skip to step 3):
   ```bash
   pipenv shell 
   ``` 
3) Enter the following command into your terminal (Note that the script accepts one parameter and that is the path to
the config file created above):  
   ```bash 
   python item_field_update.py
   ```

## Output
Execution logs will be output to the terminal as well as output to a log file in the logs/ folder located next to the 
script.