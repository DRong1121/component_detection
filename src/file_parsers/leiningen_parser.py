import re
from core.file_parsers.maven_tree_parser import parse_maven_tree_file


def parse_project_clj_file(filepath, logger):

    dependencies = list()
    is_dependency_block = False
    to_end = False
    dep_item_pattern = r'\[(?P<dep_item>.*?)\]'

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        logger.error('Exception occurs when loading project.clj file {}: {}'.format(filepath, str(e)))
        return dependencies

    for line in lines:
        line = line.strip()
        if not to_end:
            if line.startswith(':dependencies'):
                is_dependency_block = True
            if line.endswith(']]') and is_dependency_block:
                to_end = True

            if is_dependency_block and not line.startswith(';'):
                try:
                    dep_item = re.search(dep_item_pattern, line).group('dep_item')
                    if dep_item.startswith('['):
                        dep_item = dep_item.lstrip('[')

                    info = dep_item.split(' ')
                    if len(info) >= 2:
                        temp = dict()
                        temp['type'] = 'clojars'
                        namespace = info[0].split('/')[0] if '/' in info[0] else ''
                        name = info[0]
                        if info[1].startswith('"') and info[1].endswith('"'):
                            version = info[1].strip('"')
                        else:
                            version = ''
                        temp['namespace'] = namespace
                        temp['name'] = name
                        temp['version'] = version
                        temp['language'] = 'Clojure'
                        dependencies.append(temp)
                except AttributeError:
                    continue
        else:
            break

    file.close()
    return dependencies


def parse_lein_tree_file(filepath, logger):

    dependencies = parse_maven_tree_file(filepath=filepath, logger=logger)
    if dependencies:
        for i in range(0, len(dependencies)):
            dependencies[i]['type'] = 'clojars'
            dependencies[i]['language'] = 'Clojure'
    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    project_clj_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/clojure/ring/project.clj'
    log = Logger(path='../../log_dir/lein_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = list()
    clojars_deps = parse_project_clj_file(filepath=project_clj_location, logger=log)
    dep_result.extend(clojars_deps)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
