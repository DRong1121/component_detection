import os
import shutil
import json
import subprocess

from config import Config as cf
from util import is_build_gradle_file, check_pubspec_type, config_stack_programs_location

with open(os.path.join(cf.executables, 'mapper.json'), mode='r', encoding='utf-8') as f:
    mapper = json.load(f)


def get_key(mapper_dict, value):
    return [k for k, v in mapper_dict.items() if value in v]


def bash_builder(item, executable_name, logger):

    bash_dir = os.path.join(cf.executables, executable_name, 'scripts.sh')
    command_dir = os.path.split(item['file_path_absolute'])[0]
    build_file = item['file_name']

    if os.path.exists(bash_dir) and os.path.exists(command_dir):
        command = 'bash ' + bash_dir + ' ' + command_dir
        command_params = command.split()

        p = subprocess.Popen(command_params, shell=False)
        p.communicate()
        returncode = p.returncode
        if returncode == 0:
            build_status = 'success'
        else:
            build_status = 'failure'
            logger.error('Subprocess failure: {} build script execution failed on {}'.format(executable_name,
                                                                                       item['file_path_absolute']))
    else:
        build_status = 'failure'
        logger.error('Subprocess failure: {} build script does not exist on {}'.format(executable_name, bash_dir))

    build_data = {
        'build_dir': command_dir,
        'build_file': build_file,
        'build_type': executable_name,
        'build_status': build_status
    }
    return build_data


def build_with_scripts(scan_dir, search_result, logger):

    build_result = list()

    for item in search_result:
        try:
            build_data = dict()
            candidate_keys = get_key(mapper_dict=mapper, value=item['file_name'])
            if candidate_keys:
                executable_name = candidate_keys[0]
                if candidate_keys[0] == 'Dart_Pub':
                    pubspec_type = check_pubspec_type(filepath=item['file_path_absolute'], logger=logger)
                    executable_name = os.path.join(executable_name, pubspec_type)
                elif candidate_keys[0] == 'Go_Mod_Cli':
                    sum_file = os.path.join(os.path.split(item['file_path_absolute'])[0], 'go.sum')
                    if not os.path.exists(sum_file):
                        logger.warn('Subprocess failure: Go_Mod_Cli build script can not be executed: missing go.sum '
                                    'file on: {}'.format(os.path.split(item['file_path_absolute'])[0]))
                        continue
                elif candidate_keys[0] == 'Stack':
                    # make directory
                    ghc_location = os.path.join(scan_dir, 'ghc_programs')
                    if not os.path.exists(ghc_location):
                        os.makedirs(ghc_location)
                    # config project stack.yaml
                    if not config_stack_programs_location(filepath=item['file_path_absolute'], ghc_location=ghc_location,
                                                          logger=logger):
                        continue
                build_data = bash_builder(item=item, executable_name=executable_name, logger=logger)
            elif is_build_gradle_file(filepath=item['file_path_absolute']):
                build_data = bash_builder(item=item, executable_name='Gradle', logger=logger)

            if build_data:
                # logger.info('------------------------------')
                # logger.info('Build directory: ' + build_data['build_dir'])
                # logger.info('Build file: ' + build_data['build_file'])
                # logger.info('Build type: ' + build_data['build_type'])
                # logger.info('Build status: ' + build_data['build_status'])
                # logger.info('------------------------------')
                build_result.append(build_data)

                if build_data['build_type'] == 'Leiningen':
                    pom_file = os.path.join(os.path.split(item['file_path_absolute'])[0], 'pom.xml')
                    if os.path.exists(pom_file):
                        os.remove(pom_file)
                elif build_data['build_type'] == 'Stack':
                    ghc_location = os.path.join(scan_dir, 'ghc_programs')
                    if os.path.exists(ghc_location):
                        shutil.rmtree(ghc_location)
        except Exception as e:
            logger.error('Exception occurs in function build_with_scripts when executing build script on {}: {}'
                         .format(item['file_path_absolute'], str(e)))
            continue

    return build_result


if __name__ == "__main__":
    executable_name = 'Dart_Pub'
    pubspec_type = 'Dart'
    print(os.path.join(executable_name, pubspec_type))
