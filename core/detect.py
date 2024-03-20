import os

from config import CANDIDATE_FILE_LIST
from util import is_podspec_file, is_gemspec_file, is_build_gradle_file, is_package_file, is_project_file, \
    is_requirements_file, is_environment_file, is_dependencies_scala_file


def construct_candidate_file_list(scan_dir, root_name, search_depth, logger):

    result_file_list = list()

    try:
        _list = os.walk(scan_dir)
    except Exception as e:
        logger.error('Exception occurs in function construct_candidate_file_list when traversing scan_dir {}: {}'
                     .format(scan_dir, str(e)))
        return result_file_list

    if _list:
        for root, _, files in _list:
            for file in files:
                try:
                    file_type = file
                    filepath_absolute = os.path.join(root, file)

                    # system specific: Linux -> '/'
                    # TODO: cannot handle Windows -> '\\'
                    filepath_relative = os.sep + str(os.path.join(root_name,
                                                                  filepath_absolute.split(root_name + os.sep, 1)[-1]))
                    file_depth = len(os.path.split(filepath_relative)[0].split(os.sep)) - 2

                    if ((file_type in CANDIDATE_FILE_LIST)
                        or is_podspec_file(filepath_absolute)
                        or is_gemspec_file(filepath_absolute)
                        or is_build_gradle_file(filepath_absolute)
                        or is_package_file(filepath_absolute)
                        or is_project_file(filepath_absolute)
                        or is_requirements_file(filepath_absolute) or is_environment_file(filepath_absolute)
                        or is_dependencies_scala_file(filepath_absolute)) \
                            and (file_depth <= search_depth):
                        item = dict()
                        item['file_name'] = file_type
                        item['file_path_absolute'] = filepath_absolute
                        item['file_path_relative'] = filepath_relative
                        item['file_depth'] = file_depth
                        result_file_list.append(item)
                except Exception as e:
                    logger.error('Exception occurs in function construct_candidate_file_list '
                                 'when adding candidate file {}: {}'.format(os.path.join(root, file), str(e)))
                    continue

    return result_file_list


if __name__ == "__main__":

    import logging
    from core.log import Logger

    log = Logger(path='../log_dir/scala_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    scan_dir = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/scala/scalacheck'
    root_name = os.path.split(scan_dir)[-1]
    result = construct_candidate_file_list(scan_dir=scan_dir, root_name=root_name, search_depth=0, logger=log)
    if result:
        print(len(result))
        for item in result:
            print(item)
