import os
import json
import yaml
from yaml.loader import SafeLoader
import fnmatch
from functools import reduce


def is_podspec_file(filepath):
    filename = os.path.split(filepath)[-1]

    return filename.lower().endswith('.podspec')


def is_gemspec_file(filepath):
    filename = os.path.split(filepath)[-1]

    return filename.lower().endswith('.gemspec')


def is_build_gradle_file(filepath):
    filename = os.path.split(filepath)[-1]
    if filename == 'build.gradle':
        return True

    parent_dir = os.path.split(filepath)[0]
    parent_dir_name = os.path.split(parent_dir)[-1]
    return filename.lower() == (parent_dir_name + '.gradle').lower()


def is_package_file(filepath):
    filename = os.path.split(filepath)[-1].lower()
    parent_dir = os.path.split(filepath)[0]
    parent_dir_name = os.path.split(parent_dir)[-1].lower()
    package_files = (
        '*' + parent_dir_name + '*' + '.cabal',
        'package.yaml'
    )
    is_package = any(fnmatch.fnmatchcase(filename, pf) for pf in package_files)
    if is_package:
        return True
    else:
        return False


def is_project_file(filepath):
    filename = os.path.split(filepath)[-1]
    if filename.endswith('.csproj') or filename.endswith('.nuspec'):
        return True
    else:
        return False


def is_requirements_file(filepath):
    filename = os.path.split(filepath)[-1]
    req_files = (
        '*requirement*.txt',
        'requires.txt',
    )
    is_req = any(fnmatch.fnmatchcase(filename, rf) for rf in req_files)
    if is_req:
        return True

    parent_dir = os.path.split(filepath)[0]
    parent_dir_name = os.path.split(parent_dir)[-1]
    pip_extensions = ('.txt',)
    return parent_dir_name == 'requirements' and filename.endswith(pip_extensions)


def is_environment_file(filepath):
    filename = os.path.split(filepath)[-1]
    env_files = (
        '*environment*.yml',
        '*environment*.yaml',
        '*env*.yml',
        '*env*.yaml',
        'conda.yml',
    )
    is_env = any(fnmatch.fnmatchcase(filename, env) for env in env_files)
    return True if is_env else False


def is_dependencies_scala_file(filepath):
    filename = os.path.split(filepath)[-1].lower()
    parent_dir = os.path.split(filepath)[0]
    parent_dir_name = os.path.split(parent_dir)[-1].lower()

    return parent_dir_name == 'project' and filename == 'dependencies.scala'


def check_pubspec_type(filepath, logger):

    filetype = 'Dart'
    try:
        with open(file=filepath, mode='r', encoding='utf-8') as f:
            yaml_data = yaml.load(f.read(), SafeLoader)
            try:
                if 'flutter' in yaml_data['environment']:
                    filetype = 'Flutter'
            except KeyError:
                pass
    except Exception as e:
        logger.error('Subprocess exception: exception occurs in function check_pubspec_type '
                     'when loading pubspec.yaml on {}: {}'.format(filepath, str(e)))
        return filetype

    f.close()
    return filetype


def config_stack_programs_location(filepath, ghc_location, logger):
    try:
        with open(file=filepath, mode='r', encoding='utf-8') as f:
            yaml_data = yaml.load(f.read(), SafeLoader)
            yaml_data['local-programs-path'] = ghc_location
    except Exception as e:
        logger.error('Subprocess exception: exception occurs in function config_stack_programs_location '
                     'when loading stack.yaml on {}: {}'.format(filepath, str(e)))
        return 0

    try:
        with open(file=filepath, mode='w', encoding='utf-8') as f:
            yaml.dump(yaml_data, f)
    except Exception as e:
        logger.error('Subprocess exception: exception occurs in function config_stack_programs_location '
                     'when dumping stack.yaml on {}: {}'.format(filepath, str(e)))
        return 0

    f.close()
    return 1


def read_json_file(filepath, logger):
    try:
        with open(filepath, mode='r', encoding='utf-8') as f:
            json_data = json.load(f)
    except FileNotFoundError as e:
        logger.error('Error occurs in function read_json_file: {}'.format(str(e)))
        return None
    except Exception as e:
        logger.error('Exception occurs in function read_json_file on {}: {}'.format(filepath, str(e)))
        f.close()
        return None

    f.close()
    return json_data


def read_temp_json_file(filepath, logger):
    try:
        with open(filepath, mode='r', encoding='utf-8') as f:
            while True:
                line_data = f.readline()
                if line_data:
                    json_data = json.loads(line_data)
                else:
                    break
    except FileNotFoundError as e:
        logger.error('Error occurs in function read_temp_json_file: {}'.format(str(e)))
        return None
    except Exception as e:
        logger.error('Exception occurs in function read_temp_json_file on {}: {}'.format(filepath, str(e)))
        f.close()
        return None

    f.close()
    return json_data


def remove_duplicate_dict_items(data_list):
    run_function = lambda x, y: x if y in x else x + [y]
    return reduce(run_function, [[], ] + data_list)


def parse_check_result(dep_result):
    parse_result = list()
    if dep_result:
        for _, dep_item in dep_result.items():
            parse_result.extend(dep_item)
    parse_result = remove_duplicate_dict_items(data_list=parse_result)
    return parse_result


def write_check_result(result_file_path, search_result, build_result, dep_result):
    data = {
        'search_result': search_result if search_result else list(),
        'build_result': build_result if build_result else list(),
        'dep_nums': len(dep_result) if dep_result else 0,
        'dep_result': dep_result if dep_result else list()
    }
    with open(result_file_path, mode='w', encoding='utf-8') as json_file_to_write:
        json_file_to_write.write(json.dumps(data, indent=4))
    json_file_to_write.close()


def read_log(log_file_path):

    try:
        # get error info
        with open(file=log_file_path, mode='r', encoding='utf-8') as log_file:
            error_info = log_file.read().strip('\n')
    except FileNotFoundError:
        error_info = '[ERROR] Log file: {} does not exist!'.format(log_file_path)
        return error_info
    except Exception:
        error_info = '[ERROR] Exception occurs when loading log file: {}'.format(log_file_path)

    # delete log file
    if os.path.exists(log_file_path):
        os.remove(log_file_path)
    log_file.close()
    return error_info


if __name__ == "__main__":
    filepath = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/haskell/discord-haskell/stack.yaml'
    ghc_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/haskell/discord-haskell/ghc_programs'

    # result = config_stack_programs_location(filepath=filepath, ghc_location=ghc_location)
    # if result:
    #     print('config succeed')
    # else:
    #     print('config failure')

    log_file = './test.log'
    error_info = read_log(log_file_path=log_file)
    if error_info:
        print('error info: ')
        print(error_info)
    else:
        print('no error info!')
