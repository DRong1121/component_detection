import toml

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


def is_poetry_lock(filepath):
    if filepath.endswith('poetry.lock'):
        return True
    else:
        return False


def parse_pyproject(filepath, logger):

    dependencies = list()

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            content = toml.load(f=file)
    except Exception as e:
        logger.error('Exception occurs when loading pyproject.toml file {}: {}'.format(filepath, str(e)))
        return dependencies

    if not content:
        file.close()
        return dependencies

    try:
        reqs = content['build-system']['requires']
        for dep in reqs:
            req = Requirement(dep)
            temp = dict()
            temp['type'] = 'pypi'
            temp['namespace'] = ''
            name = canonicalize_name(req.name)
            temp['name'] = name
            version_str = ''

            # note: packaging.requirements.Requirement.specifier is a packaging.specifiers.SpecifierSet object
            # and a SpecifierSet._specs is
            # a set of either 'packaging.specifiers.Specifier' or 'packaging.specifiers.LegacySpecifier'
            # and each of these have a .operator and .version property

            if req.specifier:
                specifiers_set = req.specifier  # a list of packaging.specifiers.Specifier
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

            if temp['name']:
                dependencies.append(temp)
    except KeyError:
        pass

    file.close()
    return dependencies


def parse_poetry_lock(filepath, logger):

    dependencies = list()

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            content = toml.load(f=file)
    except Exception as e:
        logger.error('Exception occurs when loading poetry.lock file {}: {}'.format(filepath, str(e)))
        return dependencies

    if not content:
        file.close()
        return dependencies

    try:
        packages = content['package']
        for package in packages:
            temp = dict()
            temp['type'] = 'pypi'
            temp['namespace'] = ''
            try:
                name = package['name']
            except KeyError:
                name = ''
            temp['name'] = canonicalize_name(name)
            try:
                version = package['version']
            except KeyError:
                version = ''
            temp['version'] = version
            temp['language'] = 'Python'

            if temp['name'] and temp['version']:
                dependencies.append(temp)
    except KeyError:
        pass

    file.close()
    return dependencies


def parse_poetry_files(filepath, logger):

    if is_poetry_lock(filepath=filepath):
        dependencies = parse_poetry_lock(filepath=filepath, logger=logger)
    else:
        dependencies = parse_pyproject(filepath=filepath, logger=logger)

    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    poetry_lock_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/python/sync_with_poetry/poetry.lock'
    pyproject_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/python/sync_with_poetry/pyproject.toml'
    log = Logger(path='../../log_dir/poetry_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = list()
    # poetry_deps = parse_poetry_files(filepath=poetry_lock_location, logger=log)
    poetry_deps = parse_poetry_files(filepath=pyproject_location, logger=log)
    dep_result.extend(poetry_deps)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
