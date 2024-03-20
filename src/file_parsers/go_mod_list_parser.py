
def parse_gomod_list_file(filepath, logger):

    dependencies = list()

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        logger.error('Exception occurs when loading gomod_list.txt file {}: {}'.format(filepath, str(e)))
        return dependencies

    if len(lines) >= 1:
        lines = lines[1:]

    if lines:
        for line in lines:
            line = line.split('=>')[-1].strip()
            if line.startswith('.') or line.startswith('/'):
                continue
            dep_info = line.split(' ')
            if len(dep_info) > 1:
                name = dep_info[0]
                version = dep_info[-1].lstrip('v')
            else:
                name = dep_info[0]
                version = ''

            if '/' in name:
                namespace = '/'.join(name.split('/')[:-1])
                name = name.split('/')[-1]
            else:
                namespace = ''

            temp = dict()
            temp['type'] = 'golang'
            temp['namespace'] = namespace
            temp['name'] = name
            temp['version'] = version
            temp['language'] = 'Go'
            dependencies.append(temp)

    file.close()
    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    gomod_list_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/golang/redis-7.2.0/gomod_list.txt'
    log = Logger(path='../../log_dir/gomod_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = parse_gomod_list_file(filepath=gomod_list_location, logger=log)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
