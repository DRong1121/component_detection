import yaml
from yaml.loader import SafeLoader

from core.util import remove_duplicate_dict_items


def parse_pnpm_lock_file(filepath, is_skip, logger):

    dependencies = list()
    dev_dependencies = list()

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            data = yaml.load(file.read(), SafeLoader)
    except Exception as e:
        logger.error('Exception occurs when loading pnpm-lock.yaml file {}: {}'.format(filepath, str(e)))
        return dependencies

    try:
        for key, value in data['packages'].items():
            info = key.lstrip('/')
            if not info.startswith('file:packages'):
                name = info.rsplit('/', 1)[0]
                version = info.rsplit('/', 1)[-1].split('_')[0]
            else:
                info = info.lstrip('file:packages/').split('+')[0]
                name = info.split('@')[0]
                version = info.split('@')[-1]
            temp = dict()
            temp['type'] = 'npm'
            temp['namespace'] = ''
            temp['name'] = name
            temp['version'] = version
            temp['language'] = 'Node JS'
            try:
                if value['dev']:
                    dev_dependencies.append(temp)
                else:
                    dependencies.append(temp)
            except KeyError:
                dependencies.append(temp)
    except KeyError:
        pass

    if not is_skip and dev_dependencies:
        dependencies.extend(dev_dependencies)

    # 结果去重
    dependencies = remove_duplicate_dict_items(data_list=dependencies)

    file.close()
    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    pnpm_lock_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/javascript/monorepo/pnpm-lock.yaml'
    log = Logger(path='../../log_dir/pnpm_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = list()
    pnpm_deps = parse_pnpm_lock_file(filepath=pnpm_lock_location, is_skip=False, logger=log)
    dep_result.extend(pnpm_deps)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
