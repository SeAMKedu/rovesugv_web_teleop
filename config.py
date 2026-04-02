import yaml


with open("config.yaml", "r") as config_file:
    cfg = yaml.safe_load(config_file)
