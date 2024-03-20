import yaml
from yaml.loader import SafeLoader

from core.util import read_temp_json_file


def is_package_yaml(filepath):
    if filepath.endswith('package.yaml'):
        return True
    else:
        return False


def parse_version_list(version_list):
    for i in range(0, len(version_list)):
        version = version_list[i].strip().replace(' ', '')
        if version.startswith('=='):
            version = version.lstrip('==').strip()
            if '*' in version:
                lower = version.replace('.*', '')
                nums = lower.split('.')
                nums[-1] = str(int(nums[-1]) + 1)
                upper = '.'.join(nums)
                version = '>=' + lower + ' && ' + '<' + upper
        elif version.startswith('^>='):
            version = version.lstrip('^>=').strip()
            nums = version.split('.')
            if len(nums) == 1:
                lower = '.'.join(nums)
                nums.append('1')
                upper = '.'.join(nums)
            else:
                lower = '.'.join(nums)
                new_nums = list()
                new_nums.append(nums[0])
                new_nums.append(str(int(nums[1]) + 1))
                upper = '.'.join(new_nums)
            version = '>=' + lower + ' && ' + '<' + upper
        version_list[i] = version
    return version_list


def parse_version_str(version_str):
    if ' || ' in version_str:
        version_list = version_str.split(' || ')
        temp_list = list()
        for part in version_list:
            if ' && ' in part:
                part_list = part.split(' && ')
                part_list = parse_version_list(version_list=part_list)
                item = ' && '.join(part_list)
                temp_list.append(item)
            else:
                part_list = list()
                part_list.append(part)
                item = parse_version_list(version_list=part_list)[0]
                temp_list.append(item)
        version_str = ' || '.join(temp_list)
        return version_str
    elif ' && ' in version_str:
        version_list = version_str.split(' && ')
        temp_list = list()
        for part in version_list:
            part_list = list()
            part_list.append(part)
            item = parse_version_list(version_list=part_list)[0]
            temp_list.append(item)
        version_str = ' && '.join(temp_list)
        return version_str
    else:
        temp_list = list()
        temp_list.append(version_str)
        version_str = parse_version_list(version_list=temp_list)[0]
        return version_str


def construct_dependency_list(packages, filepath, logger):

    dependencies = list()

    if isinstance(packages, list):
        for dep_item in packages:
            if isinstance(dep_item, str):
                dep_info = dep_item.split(' ')
                name = dep_info[0]
                if len(dep_info) > 1:
                    version = ' '.join(dep_info[1:])
                else:
                    version = ''
            elif isinstance(dep_item, dict):
                try:
                    name = dep_item['name']
                except KeyError:
                    name = ''

                try:
                    version = dep_item['version']
                except KeyError:
                    version = ''
            else:
                name = ''
                version = ''

            if name:
                temp = dict()
                temp['type'] = 'hackage'
                temp['namespace'] = ''
                temp['name'] = name
                try:
                    temp['version'] = parse_version_str(version_str=version) if version else ''
                except Exception as e:
                    logger.error('Exception occurs in function parse_version_str when parsing package.yaml on {}: {}'
                                 .format(filepath, str(e)))
                    continue
                temp['language'] = 'Haskell'
                dependencies.append(temp)

    elif isinstance(packages, dict):
        for name, dep_info in packages.items():
            if isinstance(dep_info, str):
                version = dep_info
            elif isinstance(dep_info, dict):
                try:
                    version = dep_info['version']
                except KeyError:
                    version = ''
            else:
                version = ''

            temp = dict()
            temp['type'] = 'hackage'
            temp['namespace'] = ''
            temp['name'] = name
            try:
                temp['version'] = parse_version_str(version_str=version) if version else ''
            except Exception as e:
                logger.error('Exception occurs in function parse_version_str when parsing package.yaml on {}: {}'
                             .format(filepath, str(e)))
                continue
            temp['language'] = 'Haskell'
            dependencies.append(temp)

    return dependencies


def parse_package_yaml(filepath, logger):

    dependencies = list()

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            data = yaml.load(file.read(), SafeLoader)
    except Exception as e:
        logger.error('Exception occurs when loading package.yaml file {}: {}'.format(filepath, str(e)))
        return dependencies

    # add dependencies
    try:
        packages = data['dependencies']
        dependencies.extend(construct_dependency_list(packages, filepath, logger))
    except KeyError:
        pass

    # add library dependencies
    try:
        packages = data['library']['dependencies']
        dependencies.extend(construct_dependency_list(packages, filepath, logger))
    except KeyError:
        pass

    file.close()
    return dependencies


def is_end_depends_block(line):
    l = line.lower()
    if (': ' in l) or l.endswith(':'):
        return True
    elif l.startswith('if') or l.startswith('else') or l.startswith('elif'):
        return True
    else:
        return False


def is_end_package_block(line):
    l = line.lower()
    if l.startswith('library') and len(l.split(' ') > 1):
        return True
    elif l.startswith('executable'):
        return True
    elif l.startswith('test-suite'):
        return True
    elif l.startswith('benchmark'):
        return True
    elif l.startswith('foreign-library'):
        return True
    elif l.startswith('flag'):
        return True
    elif l.startswith('common'):
        return True
    elif l.startswith('source-repository'):
        return True
    elif l.startswith('custom-setup'):
        return True
    else:
        return False


def parse_package_cabal(filepath, logger):

    dependencies = list()
    is_build_depends_block = False
    is_package_block = False
    public_package_labels = ['library', 'Library']
    items = list()

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        logger.error('Exception occurs when loading cabal file {}: {}'.format(filepath, str(e)))
        return dependencies

    for line in lines:
        line = line.strip()
        if line != '\n':
            if line in public_package_labels:
                is_package_block = True
                continue

            if is_package_block:
                # TODO: find more accurate end package block flag
                if is_end_package_block(line):
                    is_build_depends_block = False
                    is_package_block = False
                    break

                if line.startswith('build-depends:') or line.startswith('Build-depends:') \
                        or line.startswith('Build-Depends:'):
                    is_build_depends_block = True
                    # 切分line
                    if line.startswith('build-depends:'):
                        line = line.split('build-depends:')[-1].strip()
                    elif line.startswith('Build-depends:'):
                        line = line.split('Build-depends:')[-1].strip()
                    elif line.startswith('Build-Depends:'):
                        line = line.split('Build-Depends:')[-1].strip()
                    # 如果切分后的line == ''，则跳转至下一行
                    if not line:
                        continue

                if is_build_depends_block:
                    # TODO: find more accurate end depends block flag
                    if is_end_depends_block(line):
                        is_build_depends_block = False
                        continue

                    if line and (not line.startswith('--')):
                        candidate_line = line.strip().strip(',').strip().replace('\n', '')
                        for item in candidate_line.split(','):
                            items.append(item.strip())

    if items:
        for dep_item in items:
            dep_info = dep_item.split(' ')
            name = dep_info[0]
            if len(dep_info) > 1:
                version = ' '.join(dep_info[1:]).strip()
            else:
                version = ''

            temp = dict()
            temp['type'] = 'hackage'
            temp['namespace'] = ''
            temp['name'] = name
            try:
                temp['version'] = parse_version_str(version_str=version) if version else ''
            except Exception as e:
                logger.error('Exception occurs in function parse_version_str when parsing cabal file on {}: {}'
                             .format(filepath, str(e)))
                continue
            temp['language'] = 'Haskell'
            dependencies.append(temp)

    file.close()
    return dependencies


def parse_stack_files(filepath, logger):

    if is_package_yaml(filepath=filepath):
        dependencies = parse_package_yaml(filepath=filepath, logger=logger)
    else:
        dependencies = parse_package_cabal(filepath=filepath, logger=logger)

    return dependencies


def parse_stack_json_file(filepath, logger):

    json_result = read_temp_json_file(filepath=filepath, logger=logger)
    dependencies = list()

    if json_result:
        for dep_item in json_result:
            try:
                name = dep_item['name']
            except KeyError:
                name = ''

            try:
                version = dep_item['version']
            except KeyError:
                version = ''

            if name:
                temp = dict()
                temp['type'] = 'hackage'
                temp['namespace'] = ''
                temp['name'] = name
                temp['version'] = version
                temp['language'] = 'Haskell'
                dependencies.append(temp)

    else:
        logger.error('Exception occurs when loading stack_deps.json!')

    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    package_yaml_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/haskell/hadolint/package.yaml'
    package_cabel_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/haskell/hoogle/hoogle.cabal'
    stack_deps_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/haskell/discord-haskell/stack_deps.json'
    log = Logger(path='../../log_dir/stack_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = list()
    # hackage_deps = parse_stack_files(filepath=package_yaml_location, logger=log)
    # hackage_deps = parse_stack_files(filepath=package_cabel_location, logger=log)
    hackage_deps = parse_stack_json_file(filepath=stack_deps_location, logger=log)
    dep_result.extend(hackage_deps)
    if dep_result:
        print(len(dep_result))
        for dep in dep_result:
            print(dep)
