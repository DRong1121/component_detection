import re
from core.util import read_json_file
from core.util import remove_duplicate_dict_items


def parse_lock_json_file(filepath, is_skip, logger):

    json_result = read_json_file(filepath=filepath, logger=logger)
    pattern = re.compile(r'[A-Za-z]', re.S)
    dep_result = list()
    dev_result = list()

    if json_result:
        # 添加子依赖
        try:
            for dep_obj, dep_info in json_result['dependencies'].items():
                temp = dict()
                temp['type'] = 'npm'
                temp['namespace'] = ''
                temp['name'] = dep_obj
                temp['version'] = dep_info['version']
                temp['language'] = 'Node JS'
                try:
                    dev = dep_info['dev']
                except KeyError:
                    dev = False
                if not len(re.findall(pattern, temp['version'].split('-')[0])):
                    if not dev:
                        dep_result.append(temp)
                    else:
                        dev_result.append(temp)

                # 添加子依赖的依赖
                try:
                    dependencies = dep_info['dependencies']
                    for sub_obj, sub_info in dependencies.items():
                        temp = dict()
                        temp['type'] = 'npm'
                        temp['namespace'] = ''
                        temp['name'] = sub_obj
                        temp['version'] = sub_info['version']
                        temp['language'] = 'Node JS'
                        try:
                            dev = sub_info['dev']
                        except KeyError:
                            dev = False
                        if not len(re.findall(pattern, temp['version'].split('-')[0])):
                            if not dev:
                                dep_result.append(temp)
                            else:
                                dev_result.append(temp)
                except KeyError:
                    pass

        except KeyError:
            pass

        # add devDependencies
        if not is_skip and dev_result:
            dep_result.extend(dev_result)

        # 结果去重
        dep_result = remove_duplicate_dict_items(data_list=dep_result)

    else:
        logger.error('Exception occurs when loading NPM lock json file!')

    return dep_result


if __name__ == "__main__":

    import logging
    from core.log import Logger

    filepath = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/javascript/axios-0.19.2/package/package-lock.json'
    log = Logger(path='../../log_dir/npm_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = parse_lock_json_file(filepath=filepath, is_skip=False, logger=log)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
