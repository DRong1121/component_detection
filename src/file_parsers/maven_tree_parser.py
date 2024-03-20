from core.util import remove_duplicate_dict_items


def parse_maven_tree_file(filepath, logger):

    dependencies = list()

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        logger.error('Exception occurs when loading maven_tree.txt file {}: {}'.format(filepath, str(e)))
        return dependencies

    for line in lines:
        if '+-' or '\\-' in line:
            if '+-' in line:
                dep_info_str = line.split('+-')[-1].strip()
                dep_info = dep_info_str.split(':')[:-1]
                if len(dep_info) >= 3:
                    temp = dict()
                    temp['type'] = 'maven'
                    temp['namespace'] = dep_info[0]
                    temp['name'] = dep_info[0] + '/' + dep_info[1]
                    temp['version'] = dep_info[-1]
                    temp['language'] = 'Java'
                    dependencies.append(temp)
            elif '\\-' in line:
                dep_info_str = line.split('\\-')[-1].strip()
                dep_info = dep_info_str.split(':')[:-1]
                if len(dep_info) >= 3:
                    temp = dict()
                    temp['type'] = 'maven'
                    temp['namespace'] = dep_info[0]
                    temp['name'] = dep_info[0] + '/' + dep_info[1]
                    temp['version'] = dep_info[-1]
                    temp['language'] = 'Java'
                    dependencies.append(temp)
    dependencies = remove_duplicate_dict_items(data_list=dependencies)

    file.close()
    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/gradle/gradle-java/spock-example/maven_tree.txt'
    log = Logger(path='../../log_dir/gradle-java_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = parse_maven_tree_file(filepath=location, logger=log)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
