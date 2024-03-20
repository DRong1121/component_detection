import dparse2

from packaging.utils import canonicalize_name
from packaging.specifiers import SpecifierSet

from core.util import read_json_file


def is_pipfile_lock(filepath):
    if filepath.endswith('Pipfile.lock'):
        return True
    else:
        return False


def parse_pipfile(filepath, logger):

    dependencies = list()

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            content = file.read()
        dep_file = dparse2.parse(content=content, file_name='Pipfile')
    except Exception as e:
        logger.error('Exception occurs when loading Pipfile {}: {}'.format(filepath, str(e)))
        return dependencies

    if not dep_file:
        file.close()
        return dependencies

    if dep_file.dependencies:
        for dependency in dep_file.dependencies:
            temp = dict()
            temp['type'] = 'pypi'
            temp['namespace'] = ''
            temp['name'] = canonicalize_name(dependency.name)
            version_str = ''
            if dependency.specs:
                specifiers_set = dependency.specs  # a list of packaging.specifiers.Specifier
                specifiers = specifiers_set._specs
                # SpecifierSet stringifies to comma-separated sorted Specifiers
                if len(specifiers) == 1:
                    specifier = list(specifiers)[0]
                    if specifier.operator in ('==', '==='):
                        version_str = specifier.version
                    elif specifier.operator == '~=':
                        nums = specifier.version.split('.')

                        lower = '.'.join(nums)
                        nums[-1] = '*'
                        upper = '.'.join(nums)
                        version_str = '>=' + lower + ', ' + '==' + upper
                    else:
                        version_str = str(specifier)
                else:
                    version_list = list()
                    for specifier in specifiers:
                        version_list.append(str(specifier))
                    version_str = ', '.join(version_list)
            temp['version'] = version_str
            temp['language'] = 'Python'
            dependencies.append(temp)

    file.close()
    return dependencies


def parse_pipfile_lock(filepath, logger):

    json_result = read_json_file(filepath=filepath, logger=logger)
    dependencies = list()

    if json_result:
        for package_type in ['default', 'develop']:

            if package_type not in json_result.keys():
                continue

            for name, meta_data in json_result[package_type].items():
                temp = dict()
                temp['type'] = 'pypi'
                temp['namespace'] = ''
                temp['name'] = canonicalize_name(name)
                version_str = ''
                try:
                    specifiers_set = SpecifierSet(meta_data['version'])
                    if specifiers_set:
                        specifiers = specifiers_set._specs
                        # SpecifierSet stringifies to comma-separated sorted Specifiers
                        if len(specifiers) == 1:
                            specifier = list(specifiers)[0]
                            if specifier.operator in ('==', '==='):
                                version_str = specifier.version
                            elif specifier.operator == '~=':
                                nums = specifier.version.split('.')

                                lower = '.'.join(nums)
                                nums[-1] = '*'
                                upper = '.'.join(nums)
                                version_str = '>=' + lower + ', ' + '==' + upper
                            else:
                                version_str = str(specifier)
                        else:
                            version_list = list()
                            for specifier in specifiers:
                                version_list.append(str(specifier))
                            version_str = ', '.join(version_list)
                except KeyError:
                    version_str = ''
                temp['version'] = version_str
                temp['language'] = 'Python'
                dependencies.append(temp)
    else:
        logger.error('Exception occurs when loading Pipfile.lock!')

    return dependencies


def parse_pipenv_files(filepath, logger):

    if is_pipfile_lock(filepath=filepath):
        dependencies = parse_pipfile_lock(filepath=filepath, logger=logger)
    else:
        dependencies = parse_pipfile(filepath=filepath, logger=logger)

    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    pipfile_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/python/requests-2.23.0/Pipfile'
    pipfile_lock_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/python/requests-2.23.0/Pipfile.lock'
    log = Logger(path='../../log_dir/pipenv_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = list()
    # pipenv_deps = parse_pipenv_files(filepath=pipfile_location, logger=log)
    pipenv_deps = parse_pipenv_files(filepath=pipfile_lock_location, logger=log)
    dep_result.extend(pipenv_deps)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
