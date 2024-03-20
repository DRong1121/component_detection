import re
from core.util import read_json_file


def is_package_resolved(filepath):
    if filepath.endswith('Package.resolved'):
        return True
    else:
        return False


def parse_package_list(candidate_list):

    dependencies = list()
    url_pattern = r'url: ".+?"'
    exact_pattern = r'.exact\("(?P<version>[0-9.]+)"\)'
    from_pattern = r'from: "(?P<version>[0-9.]+)"'
    range_pattern = r'"(?P<lower>[0-9.]+)"..."(?P<upper>[0-9.]+)"'
    upToNextMinor_pattern = r'.upToNextMinor\(from: "(?P<version>[0-9.]+)"\)'
    upToNextMajor_pattern = r'.upToNextMajor\(from: "(?P<version>[0-9.]+)"\)'

    for i in range(0, len(candidate_list)):
        candidate_line = candidate_list[i]
        # print(candidate_line)
        if re.findall(url_pattern, candidate_line):
            temp = dict()
            temp['type'] = 'swift'
            package_url = re.findall(url_pattern, candidate_line)[0].lstrip('url: "').rstrip('"')
            temp['namespace'] = '/'.join(package_url.split('/')[:-1]).split('//')[-1]
            temp['name'] = package_url.split('/')[-1].split('.')[0]
            temp['version'] = ''
            if re.search(exact_pattern, candidate_line):
                temp['version'] = re.search(exact_pattern, candidate_line).group('version')
            elif re.search(upToNextMinor_pattern, candidate_line):
                lower = re.search(upToNextMinor_pattern, candidate_line).group('version')
                nums = lower.split('.')
                if len(nums) == 3:
                    nums[-1] = '0'
                    nums[-2] = str(int(nums[-2]) + 1)
                    upper = '.'.join(nums)
                else:
                    upper = ''
                if upper:
                    temp['version'] = '>=' + lower + ', <' + upper
                else:
                    temp['version'] = '>=' + lower
            elif re.search(upToNextMajor_pattern, candidate_line):
                lower = re.search(upToNextMajor_pattern, candidate_line).group('version')
                nums = lower.split('.')
                if len(nums) == 3:
                    nums[0] = str(int(nums[0]) + 1)
                    nums[1] = '0'
                    nums[2] = '0'
                    upper = '.'.join(nums)
                else:
                    upper = ''
                if upper:
                    temp['version'] = '>=' + lower + ', <' + upper
                else:
                    temp['version'] = '>=' + lower
            elif re.search(from_pattern, candidate_line) and not temp['version']:
                temp['version'] = re.search(from_pattern, candidate_line).group('version')
            elif re.search(range_pattern, candidate_line):
                lower = re.search(range_pattern, candidate_line).group('lower')
                upper = re.search(range_pattern, candidate_line).group('upper')
                temp['version'] = '>=' + lower + ', <' + upper
            temp['language'] = 'Swift'
            dependencies.append(temp)

    return dependencies


def parse_package_swift(filepath, logger):

    dependencies = list()
    in_dependency_block = False
    empty_line_pattern = r'dependencies: \[\]'
    single_line_pattern = r'dependencies: \[.*\]'
    package_pattern = r'.package\(.+?\)'
    candidate_lines = list()

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        logger.error('Exception occurs when loading Package.swift file {}: {}'.format(filepath, str(e)))
        return dependencies

    if lines:
        for line in lines:
            line = line.strip()

            if line.startswith('dependencies: [') or line.startswith('package.dependencies = [') \
                    or line.startswith('package.dependencies += ['):
                if line.startswith('dependencies: ['):
                    if not re.findall(empty_line_pattern, line) and not re.findall(single_line_pattern, line):
                        in_dependency_block = True
                elif line.startswith('package.dependencies = [') or line.startswith('package.dependencies += ['):
                    in_dependency_block = True
                continue

            if in_dependency_block:
                if line.startswith(']'):
                    in_dependency_block = False
                    # add '] + .package' dependencies
                    if re.findall(package_pattern, line):
                        res = re.findall(package_pattern, line)
                        candidate_lines.extend(res)
                    continue

                if line.startswith('.package'):
                    # add .package dependencies
                    candidate_lines.append(line.rstrip(','))

        # handle .package dependencies
        if candidate_lines:
            try:
                dependencies = parse_package_list(candidate_list=candidate_lines)
            except Exception as e:
                logger.error('Exception occurs in function parse_package_list when parsing Package.swift on {}: {}'
                             .format(filepath, str(e)))

    file.close()
    return dependencies


def parse_package_resolved(filepath, logger):

    json_result = read_json_file(filepath=filepath, logger=logger)
    dependencies = list()

    if json_result:
        try:
            if json_result['version'] == 1:
                packages = json_result['object']['pins']
            elif json_result['version'] == 2:
                packages = json_result['pins']
            else:
                logger.error('Not supported Package.resolved version on {}'.format(filepath))
                return dependencies

            if packages:
                for package in packages:
                    temp = dict()
                    temp['type'] = 'swift'
                    package_url = ''
                    if json_result['version'] == 1:
                        package_url = package['repositoryURL']
                    elif json_result['version'] == 2:
                        package_url = package['location']
                    temp['namespace'] = '/'.join(package_url.split('/')[:-1]).split('//')[-1]
                    package_name = package_url.split('/')[-1].split('.')[0]
                    if json_result['version'] == 1:
                        temp['name'] = package['package'] if package['package'] == package_name else package_name
                    elif json_result['version'] == 2:
                        temp['name'] = package['identity'] if package['identity'] == package_name else package_name
                    temp['version'] = package['state']['version'] if package['state']['version'] else ''
                    temp['language'] = 'Swift'
                    dependencies.append(temp)
        except KeyError:
            pass

    else:
        logger.error('Exception occurs when loading Package.resolved!')

    return dependencies


def parse_swift_files(filepath, logger):

    if is_package_resolved(filepath=filepath):
        dependencies = parse_package_resolved(filepath=filepath, logger=logger)
    else:
        dependencies = parse_package_swift(filepath=filepath, logger=logger)

    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    package_swift_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/swift/SwiftLint/Package.swift'
    package_resolved_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/swift/SwiftLint/Package.resolved'
    log = Logger(path='../../log_dir/swift_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = list()
    # swift_deps = parse_swift_files(filepath=package_swift_location, logger=log)
    swift_deps = parse_swift_files(filepath=package_resolved_location, logger=log)
    dep_result.extend(swift_deps)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
