from core.util import remove_duplicate_dict_items


def parse_yarn_lock_file(filepath, logger):

    dependencies = list()

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        logger.error('Exception occurs when loading yarn.lock file {}: {}'.format(filepath, str(e)))
        return dependencies

    item = list()
    for line in lines:
        if line != '\n':
            item.append(line.strip())
        else:
            if item:
                # print(item)
                temp = dict()
                temp['type'] = 'npm'
                temp['namespace'] = ''
                temp['name'] = ''
                temp['version'] = ''
                temp['language'] = 'Node JS'
                for text in item:
                    if text.endswith(':') and text != 'dependencies:':
                        split_text = text.split(',')[0].split('@')
                        if len(split_text) > 2:
                            temp['name'] = '@' + split_text[1]
                        else:
                            temp['name'] = split_text[0].strip('"')
                    elif 'version' in text:
                        temp['version'] = text.split(' ')[-1].strip('"')
                if temp['name'] and temp['version']:
                    dependencies.append(temp)
            item = list()
    # 结果去重
    dependencies = remove_duplicate_dict_items(data_list=dependencies)

    file.close()
    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    filepath = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/javascript/synp/yarn.lock'
    log = Logger(path='../../log_dir/yarn_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = parse_yarn_lock_file(filepath=filepath, logger=log)
    if dep_result:
        print(len(dep_result))
        for dep in dep_result:
            print(dep)
