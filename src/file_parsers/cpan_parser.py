from core.util import remove_duplicate_dict_items


def parse_version_str(version):
    if version == '0':
        version = 'all'
    elif version.startswith('v'):
        version = version.lstrip('v')
    elif version.startswith('=='):
        version = version.lstrip('==').strip().lstrip('v')
    return version


def parse_cpanfile(filepath, logger):

    dependencies = list()

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        logger.error('Exception occurs when loading cpanfile {}: {}'.format(filepath, str(e)))
        return dependencies

    for line in lines:
        line = line.strip().split('#')[0].strip().rstrip(';')
        if line.startswith('requires'):
            if '\', \'' in line:
                split_line = line.split('\', \'')
                name_str = split_line[0].lstrip('requires').strip().replace('\'', '').replace('"', '')
                version = split_line[-1].strip().replace('\'', '').replace('"', '')
            elif '=>' in line:
                split_line = line.split('=>')
                name_str = split_line[0].lstrip('requires').strip().replace('\'', '').replace('"', '')
                version = split_line[-1].strip().replace('\'', '').replace('"', '')
            else:
                name_str = line.lstrip('requires').strip().replace('\'', '').replace('"', '')
                version = '0'
            split_name = name_str.split('::')
            if len(split_name) == 1:
                namespace = ''
                name = name_str
            else:
                namespace = '::'.join(split_name[:-1])
                name = split_name[-1]
            temp = dict()
            temp['type'] = 'cpan'
            temp['namespace'] = namespace
            temp['name'] = name
            try:
                temp['version'] = parse_version_str(version=str(version))
            except Exception as e:
                logger.error('Exception occurs in function parse_version_str when parsing cpanfile on {}: {}'
                             .format(filepath, str(e)))
                continue
            temp['language'] = 'Perl'
            dependencies.append(temp)
    dependencies = remove_duplicate_dict_items(data_list=dependencies)

    file.close()
    return dependencies


def parse_cpandeps(filepath, logger):

    dependencies = list()

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        logger.error('Exception occurs when loading cpan_deps.txt file {}: {}'.format(filepath, str(e)))
        return dependencies

    in_dependency_block = False
    for line in lines:
        if line.strip().startswith('Configuring'):
            in_dependency_block = True
            continue
        if in_dependency_block:
            line = line.strip()
            if '~' in line:
                split_line = line.split('~')
                name_str = split_line[0]
                version = split_line[-1]
            elif '@' in line:
                split_line = line.split('@')
                name_str = split_line[0]
                version = split_line[-1]
            else:
                name_str = line
                version = 'all'
            split_name = name_str.split('::')
            if len(split_name) == 1:
                namespace = ''
                name = name_str
            else:
                namespace = '::'.join(split_name[:-1])
                name = split_name[-1]
            temp = dict()
            temp['type'] = 'cpan'
            temp['namespace'] = namespace
            temp['name'] = name
            temp['version'] = version
            temp['language'] = 'Perl'
            dependencies.append(temp)

    file.close()
    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    cpanfile_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/perl/bmo/cpanfile'
    cpandeps_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/perl/mojo/cpan_deps.txt'
    log = Logger(path='../../log_dir/cpan_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = parse_cpanfile(filepath=cpanfile_location, logger=log)
    # dep_result = parse_cpandeps(filepath=cpandeps_location, logger=log)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
