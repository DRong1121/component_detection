import toml


def is_cargo_lock(filepath):
    if filepath.endswith('Cargo.lock'):
        return True
    else:
        return False


def parse_version_str(version_str):
    version_list = version_str.split(',')
    for i in range(0, len(version_list)):
        version = version_list[i].strip().replace(' ', '')
        if version.startswith('='):
            version_list[i] = version.lstrip('=')
            continue
        elif version.startswith('~'):
            version = version.lstrip('~')
            nums = version.split('.')
            if len(nums) == 1:
                lower = list()
                lower.append(nums[0])
                lower.append('0')
                lower.append('0')

                upper = list()
                upper.append(str(int(nums[0]) + 1))
                upper.append('0')
                upper.append('0')
                version_list[i] = '>=' + '.'.join(lower) + ', ' + '<' + '.'.join(upper)
            elif len(nums) == 2 or len(nums) == 3:
                lower = list()
                lower.append(nums[0])
                lower.append(nums[1])
                try:
                    lower.append(nums[2])
                except IndexError:
                    lower.append('0')

                upper = list()
                upper.append(nums[0])
                upper.append(str(int(nums[1]) + 1))
                upper.append('0')
                version_list[i] = '>=' + '.'.join(lower) + ', ' + '<' + '.'.join(upper)
            continue
        elif version.endswith('*'):
            if version == '*':
                version_list[i] = '>=0.0.0'
            else:
                lower = version.replace('*', '0')
                nums = lower.split('.')
                nums[-2] = str(int(nums[-2]) + 1)
                upper = '.'.join(nums)
                version_list[i] = '>=' + lower + ', ' + '<' + upper
            continue
        elif (not version.startswith('>')) and (not version.startswith('>=')) \
                and (not version.startswith('<')) and (not version.startswith('<=')) and (not version.startswith('!=')):
            version = version.lstrip('^')
            if version == '0':
                version_list[i] = '>=0.0.0, <1.0.0'
            elif version == '0.0':
                version_list[i] = '>=0.0.0, <0.1.0'
            else:
                nums = version.split('.')
                if len(nums) == 1:
                    nums.append('0')
                if len(nums) == 2:
                    nums.append('0')
                lower = '.'.join(nums)

                new_nums = list()
                for j in range(0, len(nums)):
                    if nums[j] != '0':
                        new_nums.append(str(int(nums[j]) + 1))
                        break
                    else:
                        new_nums.append(nums[j])
                if len(new_nums) == 1:
                    new_nums.append('0')
                if len(new_nums) == 2:
                    new_nums.append('0')
                upper = '.'.join(new_nums)
                version_list[i] = '>=' + lower + ', ' + '<' + upper
            continue
        else:
            version_list[i] = version
    version_str = ' && '.join(version_list)
    return version_str


def parse_cargo_toml(filepath, logger):

    dependencies = list()

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            content = toml.load(f=file)
    except Exception as e:
        logger.error('Exception occurs when loading Cargo.toml file {}: {}'.format(filepath, str(e)))
        return dependencies

    if not content:
        file.close()
        return dependencies

    # add dependencies
    try:
        deps = content['dependencies']
        for dep_name, dep_info in deps.items():
            temp = dict()
            temp['type'] = 'cargo'
            temp['namespace'] = ''
            temp['name'] = dep_name
            if isinstance(dep_info, dict):
                try:
                    temp['version'] = dep_info['version']
                except KeyError:
                    temp['version'] = ''
            elif isinstance(dep_info, str):
                try:
                    temp['version'] = parse_version_str(dep_info) if dep_info else ''
                except Exception as e:
                    logger.error('Exception occurs in function parse_version_str when parsing Cargo.toml on {}: {}'
                                 .format(filepath, str(e)))
                    continue
            temp['language'] = 'Rust'
            dependencies.append(temp)
    except KeyError:
        pass

    # add dev-dependencies
    try:
        deps = content['dev-dependencies']
        for dep_name, dep_info in deps.items():
            temp = dict()
            temp['type'] = 'cargo'
            temp['namespace'] = ''
            temp['name'] = dep_name
            if isinstance(dep_info, dict):
                try:
                    temp['version'] = dep_info['version']
                except KeyError:
                    temp['version'] = ''
            elif isinstance(dep_info, str):
                try:
                    temp['version'] = parse_version_str(dep_info) if dep_info else ''
                except Exception as e:
                    logger.error('Exception occurs in function parse_version_str when parsing Cargo.toml on {}: {}'
                                 .format(filepath, str(e)))
                    continue
            temp['language'] = 'Rust'
            dependencies.append(temp)
    except KeyError:
        pass

    file.close()
    return dependencies


def parse_cargo_lock(filepath, logger):

    dependencies = list()

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            content = toml.load(f=file)
    except Exception as e:
        logger.error('Exception occurs when loading Cargo.lock file {}: {}'.format(filepath, str(e)))
        return dependencies

    if not content:
        file.close()
        return dependencies

    try:
        packages = content['package']
        for package in packages:
            temp = dict()
            temp['type'] = 'cargo'
            temp['namespace'] = ''
            try:
                name = package['name']
            except KeyError:
                name = ''
            temp['name'] = name
            try:
                version = package['version']
            except KeyError:
                version = ''
            temp['version'] = version
            temp['language'] = 'Rust'

            if temp['name'] and temp['version']:
                dependencies.append(temp)
    except KeyError:
        pass

    file.close()
    return dependencies


def parse_cargo_files(filepath, logger):

    if is_cargo_lock(filepath=filepath):
        dep_result = parse_cargo_lock(filepath=filepath, logger=logger)
    else:
        dep_result = parse_cargo_toml(filepath=filepath, logger=logger)

    return dep_result


if __name__ == "__main__":

    import logging
    from core.log import Logger

    cargo_toml_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/rust/cargo-generate/Cargo.toml'
    cargo_lock_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/rust/cargo-generate/Cargo.lock'
    log = Logger(path='../../log_dir/cargo-generate.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = list()
    cargo_deps = parse_cargo_files(filepath=cargo_toml_location, logger=log)
    # cargo_deps = parse_cargo_files(filepath=cargo_lock_location, logger=log)
    dep_result.extend(cargo_deps)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
