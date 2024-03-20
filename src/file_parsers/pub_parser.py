import yaml
from yaml.loader import SafeLoader


def is_pubspec_lock(filepath):
    if filepath.endswith('pubspec.lock'):
        return True
    else:
        return False


def parse_version_str(version_str):

    if version_str == 'any':
        version_str = 'all'
    elif version_str.startswith('^'):
        lower = version_str.lstrip('^')
        if lower.replace('.', '').isdigit():
            nums = lower.split('.')
            if len(nums) == 3:
                if nums[0] == '0':
                    nums[1] = str(int(nums[1]) + 1)
                    nums[2] = '0'
                else:
                    nums[0] = str(int(nums[0]) + 1)
                    nums[1] = '0'
                    nums[2] = '0'
                upper = '.'.join(nums)
            else:
                upper = ''
        else:
            upper = ''

        if upper:
            version_str = '>=' + lower + ', <' + upper
        else:
            version_str = '>=' + lower

    return version_str


def parse_pubspec_yaml(filepath, is_skip, logger):

    dependencies = list()

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            data = yaml.load(file.read(), SafeLoader)
    except Exception as e:
        logger.error('Exception occurs when loading pubspec.yaml file {}: {}'.format(filepath, str(e)))
        return dependencies

    # add dependencies
    try:
        for name, version in data['dependencies'].items():
            if isinstance(version, dict):
                # {'sdk': 'flutter'} type of deps....
                if 'sdk' in version:
                    try:
                        version = 'flutter sdk: ' + parse_version_str(data['environment']['flutter'])
                    except KeyError:
                        version = 'flutter sdk'
                    except Exception as e:
                        logger.error('Exception occurs in function parse_version_str when parsing pubspec.yaml on {}: {}'
                                     .format(filepath, str(e)))
                        continue
                elif 'version' in version:
                    try:
                        version = parse_version_str(version['version'])
                    except Exception as e:
                        logger.error('Exception occurs in function parse_version_str when parsing pubspec.yaml on {}: {}'
                                     .format(filepath, str(e)))
                        continue
                else:
                    version = ''
            elif isinstance(version, str):
                try:
                    version = parse_version_str(version) if version else ''
                except Exception as e:
                    logger.error('Exception occurs in function parse_version_str when parsing pubspec.yaml on {}: {}'
                                 .format(filepath, str(e)))
                    continue
            temp = dict()
            temp['type'] = 'pubspec'
            temp['namespace'] = ''
            temp['name'] = name
            temp['version'] = version
            temp['language'] = 'Dart'
            dependencies.append(temp)
    except KeyError:
        pass

    # add dev-dependencies
    if not is_skip:
        try:
            for name, version in data['dev_dependencies'].items():
                if isinstance(version, dict):
                    # {'sdk': 'flutter'} type of deps....
                    if 'sdk' in version:
                        try:
                            version = 'flutter sdk: ' + parse_version_str(data['environment']['flutter'])
                        except KeyError:
                            version = 'flutter sdk'
                        except Exception as e:
                            logger.error(
                                'Exception occurs in function parse_version_str when parsing pubspec.yaml on {}: {}'
                                .format(filepath, str(e)))
                            continue
                    elif 'version' in version:
                        try:
                            version = parse_version_str(version['version'])
                        except Exception as e:
                            logger.error(
                                'Exception occurs in function parse_version_str when parsing pubspec.yaml on {}: {}'
                                .format(filepath, str(e)))
                            continue
                    else:
                        version = ''
                elif isinstance(version, str):
                    try:
                        version = parse_version_str(version) if version else ''
                    except Exception as e:
                        logger.error('Exception occurs in function parse_version_str when parsing pubspec.yaml on {}: {}'
                                     .format(filepath, str(e)))
                        continue
                temp = dict()
                temp['type'] = 'pubspec'
                temp['namespace'] = ''
                temp['name'] = name
                temp['version'] = version
                temp['language'] = 'Dart'
                dependencies.append(temp)
        except KeyError:
            pass

    file.close()
    return dependencies


def parse_pubspec_lock(filepath, is_skip, logger):

    dependencies = list()
    dev_dependencies = list()

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            data = yaml.load(file.read(), SafeLoader)
    except Exception as e:
        logger.error('Exception occurs when loading pubspec.lock file {}: {}'.format(filepath, str(e)))
        return dependencies

    # add packages
    try:
        for name, info in data['packages'].items():
            temp = dict()
            temp['type'] = 'pubspec'
            temp['namespace'] = ''
            temp['name'] = name
            temp['version'] = info['version']
            temp['language'] = 'Dart'
            if info['dependency'] == 'direct main' or info['dependency'] == 'transitive':
                dependencies.append(temp)
            elif info['dependency'] == 'direct dev':
                dev_dependencies.append(temp)
    except KeyError:
        pass

    if not is_skip and dev_dependencies:
        dependencies.extend(dev_dependencies)

    file.close()
    return dependencies


def parse_pubspec_files(filepath, is_skip, logger):

    if is_pubspec_lock(filepath=filepath):
        dependencies = parse_pubspec_lock(filepath=filepath, is_skip=is_skip, logger=logger)
    else:
        dependencies = parse_pubspec_yaml(filepath=filepath, is_skip=is_skip, logger=logger)

    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    pubspec_yaml_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/dart/gallery/pubspec.yaml'
    pubspec_lock_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/dart/flutter_map/pubspec.lock'
    log = Logger(path='../../log_dir/dart_pub_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = list()
    # pub_deps = parse_pubspec_files(filepath=pubspec_yaml_location, is_skip=False, logger=log)
    pub_deps = parse_pubspec_files(filepath=pubspec_lock_location, is_skip=False, logger=log)
    dep_result.extend(pub_deps)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
