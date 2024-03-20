import re


def parse_version_str(version_str):
    version_list = list()
    if 'or' in version_str:
        version_list.extend(version_str.split('or'))
    elif 'and' in version_str:
        version_list.extend(version_str.split('and'))
    else:
        version_list.append(version_str)

    for i in range(0, len(version_list)):
        version_item = version_list[i]
        if version_item.startswith('=='):
            version_list[i] = version_item.lstrip('==')
        elif version_item.startswith('~>'):
            flag = ''
            if '-' in version_item:
                flag = '-' + version_item.split('-')[-1]
                version_item = version_item.split('-')[0]

            version_item = version_item.lstrip('~>')
            if not version_item.replace('.', '').isdigit():
                flag = '.' + version_item.split('.')[-1]
                nums = version_item.split('.')[:-1]
            else:
                nums = version_item.split('.')

            if len(nums) == 1:
                nums.append('0')

            lower = '.'.join(nums)
            nums[-2] = str(int(nums[-2]) + 1)
            nums[-1] = '0'
            upper = '.'.join(nums)

            if not flag:
                version_list[i] = '>=' + lower + ', ' + '<' + upper
            else:
                version_list[i] = '>=' + lower + flag + ', ' + '<' + upper

    if 'or' in version_str:
        version_str = ' || '.join(version_list)
    elif 'and' in version_str:
        version_str = ' && '.join(version_list)
    else:
        version_str = version_list[0]
    return version_str


def parse_rebar_config_file(filepath, logger):

    dependencies = list()
    candidates = list()
    dep_block_pattern = r'\{deps,[\s\n]*?\[(?P<dep_list>(.|\n)*?)\]\}\.'
    # TODO: 优化dep_split_pattern
    #  正确解析如下字符串：
    #  {lager,"3.9.2"},recon,folsom,{dns_erlang,".*",{git,"https://github.com/dnsimple/dns_erlang.git",{branch,"main"}}}
    dep_split_pattern = r'\},\{'
    github_url_pattern = r'\{git,"(?P<github_url>.+)"'
    version_str_pattern = r'"(?P<version_str>[0-9.v]+)"'

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as raw_file:
            lines = raw_file.readlines()
    except Exception as e:
        logger.error('Exception occurs when loading raw rebar.config file {}: {}'.format(filepath, str(e)))
        return dependencies

    new_lines = list()
    for line in lines:
        if line != '\n' and not line.strip().startswith('%'):
            new_lines.append(line)
    raw_file.close()

    new_file = open(file=filepath + '.processed', mode='w', encoding='utf-8')
    for new_line in new_lines:
        new_file.write(new_line)

    try:
        with open(file=filepath + '.processed', mode='r', encoding='utf-8') as new_file:
            data = new_file.read()
    except Exception as e:
        logger.error('Exception occurs when loading processed rebar.config file {}: {}'.format(filepath + '.processed',
                                                                                               str(e)))
        return dependencies

    try:
        # 只匹配rebar.config文件中出现的第一个dep_block, 有可能不是真正的deps列表而是profiles之类
        dep_block = re.search(dep_block_pattern, data).group('dep_list').replace('\n', '').replace(' ', '')
        # print(dep_block)
        split_pattern = re.findall(dep_split_pattern, dep_block)
        if split_pattern:
            item_list = dep_block.split(split_pattern[0])
            for item in item_list:
                item = item.strip().lstrip('{')
                candidates.append(item)
        else:
            item = dep_block.strip().lstrip('{')
            candidates.append(item)

        for candidate in candidates:
            # print(candidate)
            type = 'hex'
            namespace = ''
            version_str = ''
            split_str = candidate.split(',')
            name = split_str[0].strip('\'')
            # reference to: https://rebar3.readme.io/docs/dependencies
            if len(split_str) >= 2:
                # extract namespace and version from package dependencies
                if split_str[1].strip().startswith('"') and \
                        (split_str[1].strip().endswith('"') or split_str[1].strip().endswith('"}')):
                    if '.*' not in split_str[1].strip():
                        version_str = split_str[1].strip().strip('"').strip('"}').lstrip('v')
                # extract namespace and version from source dependencies
                if not version_str:
                    if 'git' in candidate:
                        try:
                            package_url = re.search(github_url_pattern, candidate).group('github_url')
                            namespace = '/'.join(package_url.split('//')[-1].split('/')[:-1])
                        except AttributeError:
                            namespace = ''

                        try:
                            version_str = re.search(version_str_pattern, candidate).group('version_str')
                            version_str = version_str.lstrip('v')
                        except AttributeError:
                            version_str = ''

                # add dependency item
                temp = dict()
                temp['type'] = type
                temp['namespace'] = namespace
                temp['name'] = name
                try:
                    temp['version'] = parse_version_str(version_str) if version_str else ''
                except Exception as e:
                    logger.error('Exception occurs in function parse_version_str when parsing processed rebar.config '
                                 'on {}: {}'.format(filepath, str(e)))
                    continue
                temp['language'] = 'Erlang'
                dependencies.append(temp)
    except AttributeError:
        pass

    new_file.close()
    return dependencies


def parse_rebar_tree_file(filepath, logger):

    dependencies = list()
    in_dependency_block = False
    github_url_pattern = r'\((?P<github_url>.+)\)'

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        logger.error('Exception occurs when loading rebar_tree.txt file {}: {}'.format(filepath, str(e)))
        return dependencies

    for line in lines:
        if line != '\n':
            # process raw line
            processed_line = line.strip()
            if '└─' in processed_line:
                processed_line = processed_line.split('└─')[-1].strip()
            elif '├─' in processed_line:
                processed_line = processed_line.split('├─')[-1].strip()

            if processed_line.endswith('(project app)'):
                in_dependency_block = True
                continue
            if in_dependency_block:
                type = 'hex'
                namespace = ''
                if 'git' in processed_line:
                    try:
                        package_url = re.search(github_url_pattern, processed_line).group('github_url')
                        namespace = '/'.join(package_url.split('//')[-1].split('/')[:-1])
                    except AttributeError:
                        namespace = ''
                package = processed_line.rsplit('(', 1)[0].strip()
                name = package.split('─')[0]
                version = package.split('─')[-1].lstrip('v')
                temp = dict()
                temp['type'] = type
                temp['namespace'] = namespace
                temp['name'] = name
                temp['version'] = version
                temp['language'] = 'Erlang'
                dependencies.append(temp)

    file.close()
    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    rebar_config_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/erlang/hackney/rebar.config'
    rebar_tree_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/erlang/erldns/rebar_tree.txt'
    log = Logger(path='../../log_dir/rebar_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = list()
    # hex_deps = parse_rebar_config_file(filepath=rebar_config_location, logger=log)
    hex_deps = parse_rebar_tree_file(filepath=rebar_tree_location, logger=log)
    dep_result.extend(hex_deps)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
