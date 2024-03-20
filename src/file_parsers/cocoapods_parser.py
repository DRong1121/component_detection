import re
import io
import csv
import yaml
from yaml.loader import SafeLoader
from gemfileparser import GemfileParser


def is_cocoa_lock(filepath):
    if filepath.endswith('Podfile.lock'):
        return True
    else:
        return False


def parse_version_list(requirement):

    for i in range(0, len(requirement)):
        requirement[i] = requirement[i].replace(' ', '')
        req = requirement[i]
        if req.startswith('='):
            requirement[i] = req.split('=')[-1]
        elif req.startswith('~>'):
            flag = ''
            if '-' in req:
                flag = '-' + req.split('-')[-1]
                req = req.split('-')[0]

            req = req.split('~>')[-1]
            if not req.replace('.', '').isdigit():
                flag = '.' + req.split('.')[-1]
                nums = req.split('.')[:-1]
            else:
                nums = req.split('.')

            if len(nums) == 1:
                nums.append('0')

            lower = '.'.join(nums)
            nums[-2] = str(int(nums[-2]) + 1)
            nums[-1] = '0'
            upper = '.'.join(nums)

            if not flag:
                requirement[i] = '>=' + lower + ', ' + '<' + upper
            else:
                requirement[i] = '>=' + lower + flag + ', ' + '<' + upper

    return ' && '.join(requirement)


def parse_podspec(filepath, logger):

    dependencies = list()

    try:
        parser = GemfileParser(filepath=filepath)
    except Exception as e:
        logger.error('Exception occurs when loading podspec file {}: {}'.format(filepath, str(e)))
        return dependencies

    parsed_result = parser.parse()
    for key in parsed_result:
        deps = parsed_result.get(key, []) or []
        for dep in deps:
            # print(dep.name)
            # print(dep.requirement)
            temp = dict()
            temp['type'] = 'cocoapods'
            temp['namespace'] = ''
            temp['name'] = dep.name
            try:
                temp['version'] = parse_version_list(dep.requirement) if dep.requirement else ''
            except Exception as e:
                logger.error('Exception occurs in function parse_version_list when parsing podspec file on {}: {}'
                             .format(filepath, str(e)))
                continue
            temp['language'] = 'Objective C'

            if temp['name']:
                dependencies.append(temp)

    return dependencies


def parse_podfile(filepath, logger):

    dependencies = list()
    github_url_pattern = r':git\s*=>\s*\'(?P<github_url>.+?)\''
    version_str_pattern = r':tag\s*=>\s*\'(?P<version_str>[0-9.]+?)\''
    local_path_pattern = r':path\s*=>\s*\'(?P<local_path>.+?)\''
    requirement_pattern = r'(?P<requirement>([>|<|=|~>|\d]+[ ]*[0-9\.\w]+[ ,]*)+)'

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        logger.error('Exception occurs when loading Podfile {}: {}'.format(filepath, str(e)))
        return dependencies

    for line in lines:
        if line != '\n':
            line = line.strip()
            # print(line)
            if line.startswith('pod '):
                line = line.lstrip('pod ')
                dep_info = line.split(',')
                # add name
                name = dep_info[0].strip().strip('\'')

                requirement = list()
                try:
                    # add namespace (git dependency)
                    github_url = re.search(github_url_pattern, line).group('github_url')
                    namespace = '/'.join(github_url.split('/')[:-1]).split('//')[-1]
                    # add version (git dependency)
                    try:
                        version_str = re.search(version_str_pattern, line).group('version_str')
                    except AttributeError:
                        version_str = ''
                    requirement.append(version_str)
                except AttributeError:
                    # add namespace (cocoa dependency)
                    namespace = ''
                    # add version (cocoa dependency, skip local dependency)
                    try:
                        re.search(local_path_pattern, line).group('local_path')
                        # continue
                    except AttributeError:
                        if len(dep_info) > 1:
                            candidate_line = ','.join(dep_info[1:])
                            linefile = io.StringIO(candidate_line)
                            for sub_line in csv.reader(linefile, delimiter=','):
                                column_list = list()
                                for column in sub_line:
                                    stripped_column = (
                                        column.replace("'", "")
                                            .replace('"', "")
                                            .replace("%q<", "")
                                            .replace("(", "")
                                            .replace(")", "")
                                            .replace("[", "")
                                            .replace("]", "")
                                            .strip()
                                    )
                                    column_list.append(stripped_column)
                                for column in column_list:
                                    try:
                                        req = re.search(requirement_pattern, column).group('requirement')
                                        requirement.append(req)
                                    except AttributeError:
                                        continue

                temp = dict()
                temp['type'] = 'cocoapods'
                temp['namespace'] = namespace
                temp['name'] = name
                try:
                    temp['version'] = parse_version_list(requirement) if requirement else ''
                except Exception as e:
                    logger.error('Exception occurs in function parse_version_list when parsing Podfile on {}: {}'
                                 .format(filepath, str(e)))
                    continue
                temp['language'] = 'Objective C'
                dependencies.append(temp)

    file.close()
    return dependencies


def parse_pod_dep(pod):
    """
    Return a dict of (type, namespace, name, version, language) given a ``dep``
    For example:
    ' >>> expected = PackageURL.from_string('pkg:cocoapods/OHHTTPStubs@9.0.0'), '9.0.0' '
    ' >>> assert parse_dep_requirements('OHHTTPStubs (9.0.0)') == expected '
    ' >>> expected = PackageURL.from_string('pkg:cocoapods/OHHTTPStubs/NSURLSession'), None '
    ' >>> result = parse_dep_requirements('OHHTTPStubs/NSURLSession') '
    ' >>> assert result == expected, result '
    ' >>> expected = PackageURL.from_string('pkg:cocoapods/AFNetworking/Serialization@3.0.4'), '= 3.0.4' '
    ' >>> result = parse_dep_requirements(' AFNetworking/Serialization (= 3.0.4) ') '
    ' >>> assert result == expected, result '
    """
    if '(' in pod:
        name, _, version = pod.partition('(')
        version = version.strip(')( ').strip('= ')
    else:
        name = pod
        version = ''
    name = name.strip(')')

    temp = dict()
    temp['type'] = 'cocoapods'
    temp['namespace'] = ''
    temp['name'] = name.strip()
    temp['version'] = version
    temp['language'] = 'Objective C'

    return temp


def parse_podfile_lock(filepath, logger):

    dependencies = list()

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            data = yaml.load(file.read(), SafeLoader)
    except Exception as e:
        logger.error('Exception occurs when loading Podfile.lock file {}: {}'.format(filepath, str(e)))
        return dependencies

    try:
        pods = data['PODS']
        for pod in pods:
            if isinstance(pod, dict):
                for main_pod, _dep_pods in pod.items():
                    temp = parse_pod_dep(pod=main_pod)
                    dependencies.append(temp)
            elif isinstance(pod, str):
                temp = parse_pod_dep(pod=pod)
                dependencies.append(temp)
    except KeyError:
        pass

    file.close()
    return dependencies


def parse_cocoa_files(filepath, logger):

    if is_cocoa_lock(filepath=filepath):
        dep_result = parse_podfile_lock(filepath=filepath, logger=logger)
    else:
        dep_result = parse_podfile(filepath=filepath, logger=logger)

    return dep_result


if __name__ == "__main__":

    import logging
    from core.log import Logger

    podspec_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/objective_c/Criollo/Criollo.podspec'
    podfile_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/objective_c/SLOUtils/Example/Podfile'
    podfile_lock_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/objective_c/SLOUtils/Example/Podfile.lock'
    log = Logger(path='../../log_dir/cocoapods_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = list()
    # cocoa_deps = parse_podspec(filepath=podspec_location, logger=log)
    # cocoa_deps = parse_cocoa_files(filepath=podfile_location, logger=log)
    cocoa_deps = parse_cocoa_files(filepath=podfile_lock_location, logger=log)
    dep_result.extend(cocoa_deps)
    if dep_result:
        print(len(dep_result))
        for dep in dep_result:
            print(dep)
