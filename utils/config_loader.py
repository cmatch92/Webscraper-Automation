import yaml
import os

def load_config(site_name):
    """
    Loads scraping parameters from a YAML file in the config folder.
    """
    config_path = os.path.join('config', f'{site_name}.yaml')
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)
