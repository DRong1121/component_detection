import os
import re

from core.util import remove_duplicate_dict_items


def extract_candidate_build_config_files(search_result):

    candidate_dict = dict()
    candidate_list = list()
    for file_item in search_result:
        if file_item['file_name'].lower() == 'build.sbt':
            if 'type-1' not in candidate_dict.keys():
                file_item['config_file_type'] = 1
                candidate_dict['type-1'] = file_item
            else:
                if file_item['file_depth'] < candidate_dict['type-1']['file_depth']:
                    file_item['config_file_type'] = 1
                    candidate_dict['type-1'] = file_item
        elif file_item['file_name'].lower() == 'dependencies.scala':
            if 'type-2' not in candidate_dict.keys():
                file_item['config_file_type'] = 2
                candidate_dict['type-2'] = file_item
            else:
                if file_item['file_depth'] < candidate_dict['type-2']['file_depth']:
                    file_item['config_file_type'] = 2
                    candidate_dict['type-2'] = file_item

    if candidate_dict:
        for file_item in candidate_dict.values():
            candidate_list.append(file_item)

    return candidate_list


def extract_scala_version(line):

    scala_version = str()
    line = line.lower().replace('_', '')
    # print(line)
    precise_version_pattern = r'"(?P<precise_version>[0-9a-zA-Z.]+)"'
    precise_version_result = re.search(precise_version_pattern, line)
    if precise_version_result:
        scala_version = precise_version_result.group('precise_version')
        nums = scala_version.split('.')
        if nums[0] == '3':
            scala_version = nums[0]
        elif nums[0] == '2':
            scala_version = '.'.join(nums[:-1])
        else:
            scala_version = ''
        # print(scala_version)
        return scala_version
    else:
        range_version_pattern = r'scala(?P<range_version>[0-9]+)'
        range_version_result = re.search(range_version_pattern, line)
        if range_version_result:
            scala_version = range_version_result.group('range_version')
            scala_version = scala_version.split('scala')[-1]
            if scala_version[0] == '3':
                scala_version = scala_version[0]
            elif scala_version[0] == '2':
                nums = list()
                nums.append(scala_version[0])
                if len(scala_version) >= 2:
                    nums.append(scala_version[1:])
                scala_version = '.'.join(nums)
            else:
                scala_version = ''
            # print(scala_version)
            return scala_version
    return scala_version


def parse_scala_version(search_result, logger):

    scala_version = str()
    scala_pattern_1 = r'.*scalaVersions?.*\:='
    scala_pattern_2 = r'.*scalaVersions?.*='
    cross_scala_pattern_1 = r'.*crossScalaVersions?.*\:='
    cross_scala_pattern_2 = r'.*crossScalaVersions?.*='
    candidate_config_files = extract_candidate_build_config_files(search_result)
    if candidate_config_files:
        for file_item in candidate_config_files:
            try:
                with open(file=file_item['file_path_absolute'], mode='r', encoding='utf-8') as file:
                    lines = file.readlines()
                    for line in lines:
                        if line:
                            line = line.strip()
                            if file_item['config_file_type'] == 1:
                                scala_result = re.match(scala_pattern_1, line)
                                cross_scala_result = re.match(cross_scala_pattern_1, line)
                            elif file_item['config_file_type'] == 2:
                                scala_result = re.match(scala_pattern_2, line)
                                cross_scala_result = re.match(cross_scala_pattern_2, line)
                            if scala_result:
                                line = line.split('=')[-1].strip()
                                scala_version = extract_scala_version(line)
                                if scala_version:
                                    # print(scala_version)
                                    file.close()
                                    return scala_version
                            if cross_scala_result:
                                line = line.split('=')[-1].strip()
                                scala_version = extract_scala_version(line)
                                if scala_version:
                                    # print(scala_version)
                                    file.close()
                                    return scala_version
                file.close()
            except Exception as e:
                logger.error('Exception occurs when loading build.sbt or dependencies.scala file '
                             'to extract scala version'.format(file_item['file_path_absolute'], str(e)))
    return scala_version


def parse_version_str(version):
    item_pattern = r'[\[\(][0-9,.]+[\)\]]'
    match_result = re.findall(item_pattern, version)
    if match_result:
        item_list = list()
        for match_item in match_result:
            if match_item.startswith('[') and match_item.endswith(']'):
                inner_str = match_item.lstrip('[').rstrip(']')
                nums = inner_str.split(',')
                if len(nums) == 1:
                    version_item = nums[0].strip()
                else:
                    version_item = '>=' + nums[0].strip() + ', ' + '<=' + nums[-1].strip()
                item_list.append(version_item)
                continue
            elif match_item.startswith('(') and match_item.endswith(')'):
                inner_str = match_item.lstrip('(').rstrip(')')
                if inner_str.startswith(','):
                    version_item = '<' + inner_str.lstrip(',')
                elif inner_str.endswith(','):
                    version_item = '>' + inner_str.rstrip(',')
                else:
                    nums = inner_str.split(',')
                    version_item = '>' + nums[0].strip() + ', ' + '<' + nums[-1].strip()
                item_list.append(version_item)
                continue
            elif match_item.startswith('[') and match_item.endswith(')'):
                inner_str = match_item.lstrip('[').rstrip(')')
                nums = inner_str.split(',')
                if '' in nums:
                    version_item = '>=' + nums[0].strip()
                else:
                    version_item = '>=' + nums[0].strip() + ', ' + '<' + nums[-1].strip()
                item_list.append(version_item)
                continue
            elif match_item.startswith('(') and match_item.endswith(']'):
                inner_str = match_item.lstrip('(').rstrip(']')
                nums = inner_str.split(',')
                if '' in nums:
                    version_item = '<=' + nums[-1].strip()
                else:
                    version_item = '>' + nums[0].strip() + ', ' + '<=' + nums[-1].strip()
                item_list.append(version_item)
        version_str = ', '.join(item_list)
        return version_str
    else:
        return version


def parse_build_config_files(filepath, scala_version, logger):

    dependencies = list()
    # TODO: cannot handle version value in variable, such as: ' "org.slf4j" % "slf4j-log4j12" % slf4jVersion '
    dep_pattern = r'"(?P<dep_ns>.+?)"\s+%{1,3}\s+"(?P<dep_name>.+?)"\s+%\s+"(?P<dep_version>.+?)"'
    version_filter = ['early-semver', 'semver-spec', 'pvp', 'always', 'strict']

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        logger.error('Exception occurs when loading build.sbt or dependencies.scala file {}: {}'
                     .format(filepath, str(e)))
        return dependencies

    for line in lines:
        line = line.strip('\n').strip()
        if line and (not line.startswith('//')):
            dep_items = re.findall(dep_pattern, line)
            if dep_items:
                for dep_item in dep_items:
                    # print(dep_item)
                    try:
                        namespace = dep_item[0]
                    except IndexError:
                        namespace = ''

                    try:
                        name = dep_item[1]
                        if scala_version:
                            name = name + '_' + scala_version
                    except IndexError:
                        name = ''

                    try:
                        version = dep_item[2]
                    except IndexError:
                        version = ''

                    if namespace and name and version and (version not in version_filter):
                        temp = dict()
                        temp['type'] = 'maven'
                        temp['namespace'] = namespace
                        temp['name'] = namespace + '/' + name
                        try:
                            temp['version'] = parse_version_str(version=version)
                        except Exception as e:
                            logger.error(
                                'Exception occurs in function parse_version_str when parsing build.sbt '
                                'or dependencies.scala on {}: {}'.format(filepath, str(e)))
                            continue
                        temp['language'] = 'Scala'
                        dependencies.append(temp)

    file.close()
    return dependencies


def construct_tree_file_list(scan_dir):

    filepath_list = list()
    _list = os.walk(scan_dir)

    for root, _, files in _list:
        for file in files:
            filepath_absolute = os.path.join(root, file)
            if filepath_absolute.endswith('tree.json'):
                filepath_list.append(filepath_absolute)

    return filepath_list


def parse_tree_json_file(root_name, filepath_list, logger):

    dependencies = list()
    text_pattern = r'"text"\s*:\s*"(.*?)"'

    for filepath in filepath_list:
        logger.info('[+] Starting parsing tree.json file: ' + filepath)
        try:
            with open(file=filepath, mode='r', encoding='utf-8') as file:
                content = file.read()
                # print(content)
        except Exception as e:
            logger.error('Exception occurs when loading tree.json file {}: {}'.format(filepath, str(e)))
            continue

        dep_list = re.findall(text_pattern, content)
        if dep_list:
            dep_list = dep_list[1:]
            for dep_info_str in dep_list:
                dep_info = dep_info_str.split(':')
                if len(dep_info) >= 3:
                    namespace = dep_info[0]
                    name = dep_info[1].split('_')[0]
                    scala_version = dep_info[1].split('_')[-1]
                    version = dep_info[-1].split(' ')[0]
                    if name != root_name:
                        temp = dict()
                        temp['type'] = 'maven'
                        temp['namespace'] = namespace
                        if scala_version:
                            temp['name'] = namespace + '/' + name + '_' + scala_version
                        else:
                            temp['name'] = namespace + '/' + name
                        try:
                            temp['version'] = parse_version_str(version=version)
                        except Exception as e:
                            logger.error(
                                'Exception occurs in function parse_version_str when parsing tree.json on {}: {}'
                                .format(filepath, str(e)))
                            continue
                        temp['language'] = 'Scala'
                        dependencies.append(temp)

        file.close()

    # remove duplicate items
    dependencies = remove_duplicate_dict_items(data_list=dependencies)

    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger
    log = Logger(path='../../log_dir/sbt_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    # build_sbt_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/scala/scalacheck/build.sbt'
    # dep_result = parse_build_config_files(filepath=build_sbt_location, logger=log)

    # scan_dir = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/scala/ScalaPB'
    # root_name = os.path.split(scan_dir)[-1]
    # tree_file_list = construct_tree_file_list(scan_dir=scan_dir)
    # if tree_file_list:
    #     print(len(tree_file_list))
    #     for tree_file in tree_file_list:
    #         print(tree_file)
    # tree_file_list = ["/Users/rongdang/Desktop/sca-2.0/extracted_folder/scala/scalding/maple/target/tree.json"]
    # dep_result = parse_tree_json_file(root_name=root_name, filepath_list=tree_file_list, logger=log)

    search_result = [
        {
            "file_name": "build.sbt",
            "file_path_absolute": "/Users/rongdang/Desktop/sca-2.0/extracted_folder/scala/slick/build.sbt",
            "file_depth": 0
        },
        {
            "file_name": "Dependencies.scala",
            "file_path_absolute": "/Users/rongdang/Desktop/sca-2.0/extracted_folder/scala/slick/project/Dependencies.scala",
            "file_depth": 1
        }
    ]
    scala_version = parse_scala_version(search_result, log)
    dep_result = list()
    for file_item in search_result:
        result = parse_build_config_files(file_item['file_path_absolute'], scala_version, log)
        dep_result.extend(result)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
