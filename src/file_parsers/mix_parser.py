import re


def is_mix_lock(filepath):
    if filepath.endswith('mix.lock'):
        return True
    else:
        return False


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


def parse_mix_exs(filepath, logger):

    dependencies = list()
    dep_block_pattern = r'defp deps do[\s\n]*?\[[\s\n]*?(?P<dep_block>(.|\n)*?)\][\s\n]*?end'
    dep_item_pattern = r'\{.+?\}'
    github_url_pattern = r'git(hub)?:"(?P<github_url>.+?)"'
    version_str_pattern = r'(tag|ref|branch)?:"(?P<version_str>[0-9.]+)"'

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            data = file.read()
    except Exception as e:
        logger.error('Exception occurs when loading mix.exs file {}: {}'.format(filepath, str(e)))
        return dependencies

    try:
        # TODO: extract dep_block in other formats (e.g. with variables, @deps [...])
        dep_block = re.search(dep_block_pattern, data).group('dep_block')
        if dep_block:
            dep_block = dep_block.replace('\n', '').replace(' ', '')
            dep_list = re.findall(dep_item_pattern, dep_block)
            if dep_list:
                for dep_item in dep_list:
                    temp = dict()
                    temp['type'] = 'hex'
                    dep_item = dep_item.lstrip('{').rstrip('}')
                    split_str = dep_item.split(',')
                    name = split_str[0].lstrip(':')
                    namespace = ''
                    version_str = ''
                    if split_str[1].startswith('"') and split_str[1].endswith('"'):
                        version_str = split_str[1].strip('"')
                    if not version_str:
                        if 'git' in dep_item:
                            try:
                                github_url = re.search(github_url_pattern, dep_item).group('github_url')
                                namespace = '/'.join(github_url.split('/')[:-1]).split('//')[-1]
                            except AttributeError:
                                namespace = ''

                            try:
                                version_str = re.search(version_str_pattern, dep_item).group('version_str')
                            except AttributeError:
                                version_str = ''
                    temp['namespace'] = namespace
                    temp['name'] = name
                    try:
                        temp['version'] = parse_version_str(version_str) if version_str else ''
                    except Exception as e:
                        logger.error('Exception occurs in function parse_version_str when parsing mix.exs on {}: {}'
                                     .format(filepath, str(e)))
                        continue
                    temp['language'] = 'Elixir'
                    dependencies.append(temp)
    except AttributeError:
        pass

    file.close()
    return dependencies


def parse_mix_lock(filepath, logger):

    dependencies = list()
    version_pattern = r'(tag|branch)?:\s*?"(?P<version>.+)"'

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        logger.error('Exception occurs when loading mix.lock file {}: {}'.format(filepath, str(e)))
        return dependencies

    for line in lines:
        line = line.strip()
        if line != '\n' and line != '%{' and line != '}':
            try:
                line = line.split('{')[1]
                info = line.split(',')[0:3]
                namespace = ''
                name = ''
                version = ''
                if info[0].split(':')[-1] == 'hex':
                    name = info[1].strip().split(':')[-1]
                    version = info[2].strip().strip('"')
                elif info[0].split(':')[-1] == 'git':
                    info[1] = info[1].strip().strip('"')
                    namespace = '/'.join(info[1].split('//')[-1].split('/')[:-1])
                    name = info[1].split('/')[-1].rstrip('.git')
                    try:
                        version = re.search(version_pattern, line).group('version').lstrip('v')
                    except AttributeError:
                        version = ''
                if name:
                    temp = dict()
                    temp['type'] = 'hex'
                    temp['namespace'] = namespace
                    temp['name'] = name
                    temp['version'] = version
                    temp['language'] = 'Elixir'
                    dependencies.append(temp)
            except IndexError:
                continue

    file.close()
    return dependencies


def parse_mix_files(filepath, logger):

    if is_mix_lock(filepath):
        dependencies = parse_mix_lock(filepath=filepath, logger=logger)
    else:
        dependencies = parse_mix_exs(filepath=filepath, logger=logger)

    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    mix_exs_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/elixir/dataloader/mix.exs'
    mix_lock_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/elixir/earmark/mix.lock'
    log = Logger(path='../../log_dir/mix_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = list()
    # hex_deps = parse_mix_files(filepath=mix_exs_location, logger=log)
    hex_deps = parse_mix_files(filepath=mix_lock_location, logger=log)
    dep_result.extend(hex_deps)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
