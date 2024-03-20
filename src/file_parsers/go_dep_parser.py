import toml
from core.util import read_json_file


def parse_dep_file(filepath, logger):

    dependencies = list()

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            content = toml.load(f=file)
    except Exception as e:
        logger.error('Exception occurs when loading Gopkg.lock file {}: {}'.format(filepath, str(e)))
        return dependencies

    if not content:
        file.close()
        return dependencies

    try:
        deps = content['projects']
        if deps:
            for dep_item in deps:
                try:
                    name = dep_item['name']
                    if '/' in name:
                        namespace = '/'.join(name.split('/')[:-1])
                        name = name.split('/')[-1]
                    else:
                        namespace = ''
                except KeyError:
                    continue

                try:
                    version = dep_item['version'].lstrip('v')
                except KeyError:
                    try:
                        version = dep_item['revision']
                    except KeyError:
                        version = ''

                temp = dict()
                temp['type'] = 'golang'
                temp['namespace'] = namespace
                temp['name'] = name
                temp['version'] = version
                temp['language'] = 'Go'
                dependencies.append(temp)
    except KeyError:
        pass

    file.close()
    return dependencies


def parse_godep_file(filepath, logger):

    json_result = read_json_file(filepath, logger)
    dependencies = list()

    if json_result:
        try:
            deps = json_result['Deps']
            for dep in deps:
                ns_name = dep['ImportPath'].split('/')
                namespace = '/'.join(ns_name[:-1])
                name = ns_name[-1]
                try:
                    version = dep['Comment'].lstrip('v')
                except KeyError:
                    version = ''
                temp = dict()
                temp['type'] = 'golang'
                temp['namespace'] = namespace
                temp['name'] = name
                temp['version'] = version
                temp['language'] = 'Go'
                dependencies.append(temp)
        except KeyError:
            pass
    else:
        logger.error('Exception occurs when loading Godeps.json file: {}'.format(filepath))

    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    dep_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/golang/dep-test/Gopkg.lock'
    godep_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/golang/With-Godeps/Godeps/Godeps.json'
    log = Logger(path='../../log_dir/godep_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    # dep_result = parse_dep_file(filepath=dep_location, logger=log)
    dep_result = parse_godep_file(filepath=godep_location, logger=log)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
