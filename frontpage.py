import os
import argparse
import configparser
import json
import glob
import shutil
from pathlib import Path
# 3rd Party
# -----------------------------------------------------------------------------
import yaml
from yaml.loader import SafeLoader
from jinja2 import (
    Environment,
    PackageLoader,
    select_autoescape,
    FileSystemLoader
)


__version__ = "0.1.0"


def open_cfg(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    return config


def open_cfg_json(file_path):
    return json.load(open(file_path))


def open_yaml(file_path):
    with open(file_path, 'r') as f:
        data = yaml.load(f, Loader=SafeLoader)
        return data


def build_context():
    ret = {}
    yaml_data_file_paths = glob.glob("./data/*.yaml")
    for file_path in yaml_data_file_paths:
        yaml_data = open_yaml(file_path)
        ctx_key = os.path.basename(file_path).split('.')[0]
        ret[ctx_key] = yaml_data
    return ret


def get_theme_templates_file_names(theme_name):
    template_file_names = glob.glob(f"./themes/{theme_name}/*.html")
    for path in template_file_names:
        yield os.path.basename(path)


def get_theme_static_asset_file_paths(theme_name):
    theme_folder_path = f'./themes/{theme_name}'
    static_assets_folder_path = f'{theme_folder_path}/static/'
    exp_path = os.path.expanduser(static_assets_folder_path)
    print(f'Listing Statics from {static_assets_folder_path}')
    for root, dirs, files in os.walk(exp_path):
        for file_path in files:
            yield os.path.join(root, file_path)


def get_custom_static_asset_file_paths():
    static_assets_folder_path = f'./static/'
    exp_path = os.path.expanduser(static_assets_folder_path)
    print(f'Listing Statics from {static_assets_folder_path}')
    for root, dirs, files in os.walk(exp_path):
        for file_path in files:
            yield os.path.join(root, file_path)


def build(args):
    env = args.env
    cfg = open_cfg(args.config)
    theme_name = cfg["Basic"]["theme"]
    env = Environment(
        loader=FileSystemLoader(f"themes/{theme_name}"),
        autoescape=select_autoescape()
    )

    data = {'env': env, 'config': cfg} | build_context()
    dist_folder_path = './dist/'

    # Rendering Templates
    # -------------------------------------------------------------------------
    for template_file_name in get_theme_templates_file_names(theme_name):
        path = Path(f'{dist_folder_path}/{template_file_name}')
        print(f'Rendering template {template_file_name} to {path}')
        path.parent.mkdir(parents=True, exist_ok=True)
        template = env.get_template(template_file_name)
        rendered_template = template.render(data=data)
        with open(path, 'w') as f:
            f.write(rendered_template)

    # Copying Statics
    # -------------------------------------------------------------------------
    for asset_file_path in get_theme_static_asset_file_paths(theme_name):
        theme_folder_path = f'./themes/{theme_name}/static/'
        dist_asset_file_path = Path(asset_file_path.replace(
            theme_folder_path,
            dist_folder_path,
            ))
        print(f'Copying {asset_file_path} to {dist_asset_file_path}')
        dist_asset_file_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(asset_file_path, dist_asset_file_path)

    for asset_file_path in get_custom_static_asset_file_paths():
        dist_asset_file_path = Path(asset_file_path.replace(
            './static/',
            dist_folder_path,
            ))
        print(f'Copying {asset_file_path} to {dist_asset_file_path}')
        dist_asset_file_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(asset_file_path, dist_asset_file_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="frontpage",
        description="static landpage generator",
        )

    parser.add_argument(
        "-v", "--version", action="version", version=f"{__version__}")

    parser.add_argument(
        "-c", "--config", type=str, default="./frontpage.ini")

    sparser = parser.add_subparsers(help="actions help")

    build_parser = sparser.add_parser(
        "build",
        help="build distribution",
        )
    #build_parser.add_argument(
    #    '-d',
    #    '--delay',
    #    type=int,
    #    default=10,
    #    help='delay (secs) for next batch',
    #    )
    build_parser.add_argument(
        '-e',
        '--env',
        type=str,
        default='dev',
        help="Environment you're building for",
        )
    build_parser.set_defaults(func=build)

    args = parser.parse_args()
    args.func(args)
