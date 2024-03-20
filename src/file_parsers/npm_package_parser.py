import re
from core.util import read_json_file


def parse_version_list(version_list):
    # for loop
    for i in range(0, len(version_list)):
        # print(version_list[i])
        # 切分版本号与版本号后缀
        version = version_list[i].strip().split('-')[0]
        if '-' in version_list[i]:
            flag = '-' + version_list[i].strip().split('-')[-1]
        else:
            flag = ''

        # all版本
        if version == '*' or version == 'x':
            version_list[i] = 'all' + flag
            continue

        # 替换首字符等号
        if version.startswith('='):
            version = version.replace('=', '')

        # 解析版本号（各种情况）
        if not version.startswith('~') and not version.startswith('^'):
            if version.startswith('>'):
                version = version.strip('>')
                version = version.replace('.x', '')
                version = version.replace('.*', '')

                nums = version.split('.')
                if len(nums) < 3:
                    nums[-1] = str(int(nums[-1]) + 1)
                    if len(nums) == 1:
                        nums.append('0')
                    if len(nums) == 2:
                        nums.append('0')
                    version = '.'.join(nums)
                    version_list[i] = '>=' + version + flag
                else:
                    version_list[i] = '>' + version + flag
                continue
            elif version.startswith('!=') or version.startswith('>=') \
                    or version.startswith('<') or version.startswith('<='):
                version = version.replace('x', '0')
                version = version.replace('*', '0')

                nums = version.split('.')
                if len(nums) == 1:
                    nums.append('0')
                if len(nums) == 2:
                    nums.append('0')
                version = '.'.join(nums)
                version_list[i] = version + flag
                continue
            else:
                version = version.replace('.x', '')
                version = version.replace('.*', '')

                nums = version.split('.')
                if len(nums) < 3:
                    version = '~' + version
                else:
                    version_list[i] = version + flag
                    continue

        if version.startswith('~'):
            version = version.strip('~')
            version = version.replace('.x', '')
            version = version.replace('.*', '')

            nums = version.split('.')
            upper_nums = version.split('.')
            if len(nums) < 3:
                upper_nums[-1] = str(int(upper_nums[-1]) + 1)

                if len(nums) == 1:
                    nums.append('0')
                if len(nums) == 2:
                    nums.append('0')
                if len(upper_nums) == 1:
                    upper_nums.append('0')
                if len(upper_nums) == 2:
                    upper_nums.append('0')
            else:
                upper_nums[-2] = str(int(upper_nums[-2]) + 1)
                upper_nums[-1] = '0'

            lower = '.'.join(nums) + flag
            upper = '.'.join(upper_nums)
            version_list[i] = '>=' + lower + ', ' + '<' + upper
            continue

        elif version.startswith('^'):
            version = version.strip('^')
            version = version.replace('.x', '')
            version = version.replace('.*', '')

            nums = version.split('.')

            upper_nums = list()
            for index in range(0, len(nums)):
                if nums[index] == '0':
                    upper_nums.append(nums[index])
                else:
                    upper_nums.append(str(int(nums[index]) + 1))
                    break

            if len(nums) == 1:
                nums.append('0')
            if len(nums) == 2:
                nums.append('0')
            if len(upper_nums) == 1:
                upper_nums.append('0')
            if len(upper_nums) == 2:
                upper_nums.append('0')

            lower = '.'.join(nums) + flag
            upper = '.'.join(upper_nums)
            version_list[i] = '>=' + lower + ', ' + '<' + upper
    # end for
    # for i in range(0, len(version_list)):
    #     print(version_list[i])
    return version_list


def parse_version_str(version_str):
    version_str = version_str.replace('^ ', '^')
    version_str = version_str.replace('~ ', '~')
    version_str = version_str.replace('~> ', '~')
    version_str = version_str.replace('> ', '>')
    version_str = version_str.replace('>= ', '>=')
    version_str = version_str.replace('< ', '<')
    version_str = version_str.replace('<= ', '<=')
    version_str = version_str.replace('= ', '=')
    if version_str:
        if ' - ' in version_str:
            version_list = version_str.split(' - ')
            lower = version_list[0].strip().split('-')[0]
            if '-' in lower:
                lower_flag = '-' + version_list[0].strip().split('-')[-1]
            else:
                lower_flag = ''
            upper = version_list[-1].strip().split('-')[0]
            if '-' in upper:
                upper_flag = '-' + version_list[-1].strip().split('-')[-1]
            else:
                upper_flag = ''

            upper_nums = upper.split('.')
            if len(upper_nums) < 3:
                upper_nums[-1] = str(int(upper_nums[-1]) + 1)
                if len(upper_nums) == 1:
                    upper_nums.append('0')
                if len(upper_nums) == 2:
                    upper_nums.append('0')
                upper = '.'.join(upper_nums)
                version_str = '>=' + lower + lower_flag + ', ' + '<' + upper + upper_flag
            else:
                version_str = '>=' + lower + lower_flag + ', ' + '<=' + upper + upper_flag
        elif ' || ' in version_str:
            version_list = version_str.split(' || ')
            temp_list = list()
            for part in version_list:
                if ' ' in part:
                    part_list = part.split(' ')
                    part_list = parse_version_list(version_list=part_list)
                    item = ', '.join(part_list)
                    temp_list.append(item)
                elif ',' in part:
                    part_list = part.split(',')
                    part_list = parse_version_list(version_list=part_list)
                    item = ', '.join(part_list)
                    temp_list.append(item)
                else:
                    part_list = list()
                    part_list.append(part)
                    item = parse_version_list(version_list=part_list)[0]
                    temp_list.append(item)
            version_str = ' || '.join(temp_list)
        elif ' ' in version_str:
            version_list = version_str.split(' ')
            version_list = parse_version_list(version_list=version_list)
            version_str = ', '.join(version_list)
        elif ',' in version_str:
            version_list = version_str.split(',')
            version_list = parse_version_list(version_list=version_list)
            version_str = ', '.join(version_list)
        else:
            version_list = list()
            version_list.append(version_str)
            version_str = parse_version_list(version_list=version_list)[0]
    return version_str


def parse_package_json_file(filepath, is_skip, logger):

    json_result = read_json_file(filepath=filepath, logger=logger)
    pattern = re.compile(r'[A-Za-z]', re.S)
    dependencies = list()

    if json_result:
        # add dependencies
        try:
            for key, value in json_result['dependencies'].items():
                if not len(re.findall(pattern, value.split('-')[0])):
                    temp = dict()
                    temp['type'] = 'npm'
                    temp['namespace'] = ''
                    temp['name'] = key
                    try:
                        temp['version'] = parse_version_str(version_str=value)
                    except Exception as e:
                        logger.error('Exception occurs in function parse_version_str when parsing package.json on {}: {}'
                                     .format(filepath, str(e)))
                        continue
                    temp['language'] = 'Node JS'
                    dependencies.append(temp)
        except KeyError:
            pass

        # 若设置不跳过devDependencies
        if not is_skip:
            # add devDependencies
            try:
                for key, value in json_result['devDependencies'].items():
                    if not len(re.findall(pattern, value.split('-')[0])):
                        temp = dict()
                        temp['type'] = 'npm'
                        temp['namespace'] = ''
                        temp['name'] = key
                        try:
                            temp['version'] = parse_version_str(version_str=value)
                        except Exception as e:
                            logger.error(
                                'Exception occurs in function parse_version_str when parsing package.json on {}: {}'
                                .format(filepath, str(e)))
                            continue
                        temp['language'] = 'Node JS'
                        dependencies.append(temp)
            except KeyError:
                pass
    else:
        logger.error('Exception occurs when loading NPM package json file!')

    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    filepath = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/javascript/axios-0.19.2/package/package.json'
    log = Logger(path='../../log_dir/npm_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = parse_package_json_file(filepath=filepath, is_skip=False, logger=log)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
