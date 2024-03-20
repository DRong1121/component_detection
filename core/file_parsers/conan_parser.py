from core.util import read_json_file, read_temp_json_file


def parse_conan_lock(filepath, logger):

    json_result = read_json_file(filepath=filepath, logger=logger)
    dependencies = list()

    if json_result:
        try:
            nodes = json_result['graph_lock']['nodes']
            for _, value in nodes.items():
                try:
                    ref = value['ref']
                    name = ref.split('/')[0]
                    if '/' in ref:
                        version = ref.split('/')[-1].split('@')[0]
                    else:
                        version = ''
                    temp = dict()
                    temp['type'] = 'conan'
                    temp['namespace'] = ''
                    temp['name'] = name
                    temp['version'] = version
                    temp['language'] = 'C/C++'
                    dependencies.append(temp)
                except KeyError:
                    continue
        except KeyError:
            pass

    else:
        logger.error('Exception occurs when loading conan.lock file: {}'.format(filepath))

    return dependencies


def parse_conan_result(filepath, logger):

    json_result = read_temp_json_file(filepath=filepath, logger=logger)
    dependencies = list()

    if json_result:
        for dep_item in json_result:
            try:
                ref = dep_item['reference']
                name = ref.split('/')[0]
                if '/' in ref:
                    version = ref.split('/')[-1].split('@')[0]
                else:
                    version = ''
                if name != 'conanfile.py' and name != 'conanfile.txt':
                    temp = dict()
                    temp['type'] = 'conan'
                    temp['namespace'] = ''
                    temp['name'] = name
                    temp['version'] = version
                    temp['language'] = 'C/C++'
                    dependencies.append(temp)
            except KeyError:
                continue

    else:
        logger.error('Exception occurs when loading conan_result.json file: {}'.format(filepath))

    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    conan_lock_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/conan/conan_test/conan.lock'
    conan_result_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/conan/conan_test/conan_deps.json'
    log = Logger(path='../../log_dir/conan_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    # dep_result = parse_conan_lock(filepath=conan_lock_location, logger=log)
    dep_result = parse_conan_result(filepath=conan_result_location, logger=log)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
