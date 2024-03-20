
def is_cartfile_resolved(filepath):
    if filepath.endswith('Cartfile.resolved'):
        return True
    else:
        return False


def parse_version_str(version):

    if version.startswith('=='):
        version = version.split('==')[-1]
    elif version.startswith('~>'):
        flag = ''
        if '-' in version:
            flag = '-' + version.split('-')[-1]
            version = version.split('-')[0]

        version = version.split('~>')[-1]
        if not version.replace('.', '').isdigit():
            flag = '.' + version.split('.')[-1]
            nums = version.split('.')[:-1]
        else:
            nums = version.split('.')

        if len(nums) == 1:
            nums.append('0')

        lower = '.'.join(nums)
        nums[-2] = str(int(nums[-2]) + 1)
        nums[-1] = '0'
        upper = '.'.join(nums)

        if not flag:
            version = '>=' + lower + ', ' + '<' + upper
        else:
            version = '>=' + lower + flag + ', ' + '<' + upper

    return version


def parse_cartfile(filepath, logger):

    dependencies = list()
    urls = ['https://', 'http://', 'git://', 'git@', 'ssh://']

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        logger.error('Exception occurs when loading Cartfile {}: {}'.format(filepath, str(e)))
        return dependencies

    for line in lines:
        if line != '\n':
            line = line.strip()
            if line.startswith('github'):
                line = line.lstrip('github').strip()
                info = line.split(' ')
                if len(info) >= 1:
                    name = info[0].strip('"')
                    for url_starter in urls:
                        if name.startswith(url_starter):
                            name = name.split(url_starter)[-1]
                            break
                    if '/' in name:
                        namespace = '/'.join(name.split('/')[:-1])
                        name = name.split('/')[-1]
                    else:
                        namespace = ''

                if len(info) >= 2:
                    version = ''.join(info[1:]).strip('"').lstrip('v')
                else:
                    version = ''

                temp = dict()
                temp['type'] = 'cocoapods'
                temp['namespace'] = namespace
                temp['name'] = name
                try:
                    temp['version'] = parse_version_str(version) if version else ''
                except Exception as e:
                    logger.error('Exception occurs in function parse_version_str when parsing Cartfile on {}: {}'
                                 .format(filepath, str(e)))
                    continue
                temp['language'] = 'Objective C'
                dependencies.append(temp)

            elif line.startswith('git'):
                line = line.lstrip('git').strip()
                info = line.split(' ')
                if len(info) >= 1:
                    name = info[0].strip('"').rstrip('.git')
                    for url_starter in urls:
                        if name.startswith(url_starter):
                            name = name.split(url_starter)[-1]
                            break
                    if '/' in name:
                        namespace = '/'.join(name.split('/')[:-1])
                        name = name.split('/')[-1]
                    else:
                        namespace = ''

                if len(info) >= 2:
                    version = ''.join(info[1:]).strip('"').lstrip('v')
                else:
                    version = ''

                temp = dict()
                temp['type'] = 'cocoapods'
                temp['namespace'] = namespace
                temp['name'] = name
                try:
                    temp['version'] = parse_version_str(version) if version else ''
                except Exception as e:
                    logger.error('Exception occurs in function parse_version_str when parsing Cartfile on {}: {}'
                                 .format(filepath, str(e)))
                    continue
                temp['language'] = 'Objective C'
                dependencies.append(temp)

            elif line.startswith('binary'):
                continue

    file.close()
    return dependencies


def parse_cartfile_resolved(filepath, logger):

    dependencies = list()
    urls = ['https://', 'http://', 'git://', 'git@', 'ssh://']

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        logger.error('Exception occurs when loading Cartfile.resolved file {}: {}'.format(filepath, str(e)))
        return dependencies

    for line in lines:
        if line != '\n':
            line = line.strip()
            if line.startswith('github'):
                line = line.lstrip('github').strip()
                info = line.split(' ')
                if len(info) >= 1:
                    name = info[0].strip('"')
                    for url_starter in urls:
                        if name.startswith(url_starter):
                            name = name.split(url_starter)[-1]
                            break
                    if '/' in name:
                        namespace = '/'.join(name.split('/')[:-1])
                        name = name.split('/')[-1]
                    else:
                        namespace = ''

                if len(info) >= 2:
                    version = info[1].strip('"').lstrip('v')
                else:
                    version = ''

                temp = dict()
                temp['type'] = 'cocoapods'
                temp['namespace'] = namespace
                temp['name'] = name
                temp['version'] = version
                temp['language'] = 'Objective C'
                dependencies.append(temp)

            elif line.startswith('git'):
                line = line.lstrip('git').strip()
                info = line.split(' ')
                if len(info) >= 1:
                    name = info[0].strip('"').rstrip('.git')
                    for url_starter in urls:
                        if name.startswith(url_starter):
                            name = name.split(url_starter)[-1]
                            break
                    if '/' in name:
                        namespace = '/'.join(name.split('/')[:-1])
                        name = name.split('/')[-1]
                    else:
                        namespace = ''

                if len(info) >= 2:
                    version = info[1].strip('"').lstrip('v')
                else:
                    version = ''

                temp = dict()
                temp['type'] = 'cocoapods'
                temp['namespace'] = namespace
                temp['name'] = name
                temp['version'] = version
                temp['language'] = 'Objective C'
                dependencies.append(temp)

            elif line.startswith('binary'):
                continue

    file.close()
    return dependencies


def parse_carthage_files(filepath, logger):

    if is_cartfile_resolved(filepath=filepath):
        dependencies = parse_cartfile_resolved(filepath=filepath, logger=logger)
    else:
        dependencies = parse_cartfile(filepath=filepath, logger=logger)

    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    cartfile_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/objective_c/CartfileTest/Cartfile'
    cartfile_resolved_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/objective_c/CartfileTest/Cartfile.resolved'
    log = Logger(path='../../log_dir/CartfileTest.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = list()
    # cocoa_deps = parse_carthage_files(filepath=cartfile_location, logger=log)
    cocoa_deps = parse_carthage_files(filepath=cartfile_resolved_location, logger=log)
    dep_result.extend(cocoa_deps)
    if dep_result:
        print(len(dep_result))
        for dep in dep_result:
            print(dep)
