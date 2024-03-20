import json
import yaml
from yaml.loader import SafeLoader

from core.util import remove_duplicate_dict_items


def extract_cran_dependencies(yaml_data):

    dependencies = list()

    if yaml_data:
        # add depends
        depends = yaml_data.get('Depends') or ''
        for dependency in depends.split(',\n'):
            version = ''
            for splitter in ('==', '>=', '<=', '>', '<'):
                if splitter in dependency:
                    splits = dependency.split(splitter)
                    # Replace the package name and keep the relationship and version
                    # For example: R (>= 2.1)
                    version = dependency.replace(splits[0], '').strip().strip(')').strip()
                    name = splits[0].strip().strip('(').strip()
                    break
                else:
                    name = dependency

            if name and name != 'R':
                temp = dict()
                temp['type'] = 'cran'
                temp['namespace'] = ''
                temp['name'] = name
                temp['version'] = version.replace(' ', '').lstrip('==')
                temp['language'] = 'R'
                dependencies.append(temp)

        # add imports
        imports = yaml_data.get('Imports') or ''
        for dependency in imports.split(',\n'):
            version = ''
            for splitter in ('==', '>=', '<=', '>', '<'):
                if splitter in dependency:
                    splits = dependency.split(splitter)
                    # Replace the package name and keep the relationship and version
                    # For example: R (>= 2.1)
                    version = dependency.replace(splits[0], '').strip().strip(')').strip()
                    name = splits[0].strip().strip('(').strip()
                    break
                else:
                    name = dependency

            if name:
                temp = dict()
                temp['type'] = 'cran'
                temp['namespace'] = ''
                temp['name'] = name
                temp['version'] = version.replace(' ', '').lstrip('==')
                temp['language'] = 'R'
                dependencies.append(temp)

    return dependencies


def parse_cran_description(filepath, logger):
    """
    Parse a CRAN DESCRIPTION file as YAML and return a list of dependencies.
    """
    yaml_lines = list()
    dependencies = list()

    try:
        with open(filepath, mode='r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        logger.error('Exception occurs when loading DESCRIPTION file {}: {}'.format(filepath, str(e)))
        return dependencies

    for line in lines:
        if not line:
            continue
        line = line.replace('\'', '')
        line = line.replace('`', '')
        yaml_lines.append(line)

    try:
        data = yaml.load('\n'.join(yaml_lines), SafeLoader)
        dependencies = extract_cran_dependencies(yaml_data=data)
    except Exception as e:
        logger.error('Exception occurs in function parse_cran_description when constructing yaml data '
                     'and extracting cran dependencies on {}: {}'.format(filepath, str(e)))

    file.close()
    return dependencies


def parse_cran_lock(filepath, logger):

    dependencies = list()

    try:
        # 如果是json文件，获取packages列表及第一层传递依赖
        with open(filepath, mode='r', encoding='utf-8') as json_file:
            json_data = json.load(json_file)
    except Exception:
        try:
            # 如果不是json文件
            with open(filepath, mode='r', encoding='utf-8') as lock_file:
                lines = lock_file.readlines()
        except Exception as e:
            logger.error('Exception occurs when loading packrat.lock file {}: {}'.format(filepath, str(e)))
            return dependencies

        items = list()
        info = list()
        for line in lines:
            if line != '\n':
                info.append(line.strip())
            else:
                item = dict()
                for l in info:
                    key = l.split(':')[0].strip()
                    value = l.split(':')[-1].strip()
                    item[key] = value
                items.append(item)
                info = list()
        if info:
            item = dict()
            for l in info:
                key = l.split(':')[0].strip()
                value = l.split(':')[-1].strip()
                item[key] = value
            items.append(item)

        if items:
            for i in range(1, len(items)):
                temp = dict()
                temp['type'] = 'cran'
                temp['namespace'] = ''
                temp['name'] = items[i]['Package']
                temp['version'] = items[i]['Version']
                temp['language'] = 'R'
                dependencies.append(temp)
        lock_file.close()
        dependencies = remove_duplicate_dict_items(data_list=dependencies)
        return dependencies

    try:
        packages = json_data['packages']
        for package in packages:
            temp = dict()
            temp['type'] = 'cran'
            temp['namespace'] = ''
            temp['name'] = package['name']
            temp['version'] = package['version']
            temp['language'] = 'R'
            dependencies.append(temp)
            if package['depends']:
                for dep in package['depends']:
                    temp = dict()
                    temp['type'] = 'cran'
                    temp['namespace'] = ''
                    temp['name'] = dep['name']
                    temp['version'] = dep['version']
                    temp['language'] = 'R'
                    dependencies.append(temp)
    except KeyError:
        pass
    json_file.close()
    dependencies = remove_duplicate_dict_items(data_list=dependencies)
    return dependencies


def parse_cran_files(filepath, logger):

    dependencies = list()

    if filepath.endswith('DESCRIPTION'):
        dependencies = parse_cran_description(filepath=filepath, logger=logger)
    elif filepath.endswith('packrat.lock'):
        dependencies = parse_cran_lock(filepath=filepath, logger=logger)

    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    description_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/R/dplyr/DESCRIPTION'
    lock_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/R/Try_packrat/packrat/packrat.lock'
    log = Logger(path='../../log_dir/R_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    # dep_result = parse_cran_files(filepath=description_location, logger=log)
    dep_result = parse_cran_files(filepath=lock_location, logger=log)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
