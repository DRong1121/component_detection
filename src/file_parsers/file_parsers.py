import sys
import os
import json

sys.path.append('.')
sys.path.append('..')
from core.config import Config as cf
from core.util import remove_duplicate_dict_items
from core.util import is_podspec_file, is_gemspec_file, is_build_gradle_file, is_package_file, is_project_file, \
    is_requirements_file, is_environment_file, is_dependencies_scala_file
from core.file_parsers.cargo_parser import parse_cargo_files
from core.file_parsers.carthage_parser import parse_carthage_files
from core.file_parsers.cocoapods_parser import parse_podspec, parse_cocoa_files
from core.file_parsers.composer_parser import parse_composer_files
from core.file_parsers.conan_parser import parse_conan_lock
from core.file_parsers.conda_parser import parse_environment_file
from core.file_parsers.cpan_parser import parse_cpanfile, parse_cpandeps
from core.file_parsers.cran_parser import parse_cran_files
from core.file_parsers.gemfile_lock_parser import parse_gemfile_lock_file
from core.file_parsers.go_dep_parser import parse_godep_file, parse_dep_file
from core.file_parsers.go_mod_parser import parse_gomod_files
from core.file_parsers.go_mod_list_parser import parse_gomod_list_file
from core.file_parsers.gradle_parser import parse_build_gradle_file, parse_gradle_tree_file
from core.file_parsers.leiningen_parser import parse_project_clj_file, parse_lein_tree_file
from core.file_parsers.maven_pom_parser import parse_maven_pom_file
from core.file_parsers.maven_tree_parser import parse_maven_tree_file
from core.file_parsers.mix_parser import parse_mix_files
from core.file_parsers.npm_package_parser import parse_package_json_file
from core.file_parsers.npm_lock_parser import parse_lock_json_file
from core.file_parsers.nuget_parser import parse_nuget_files
from core.file_parsers.pip_parser import parse_pip_files
from core.file_parsers.pipenv_parser import parse_pipenv_files
from core.file_parsers.pnpm_lock_parser import parse_pnpm_lock_file
from core.file_parsers.poetry_parser import parse_poetry_files
from core.file_parsers.pub_parser import parse_pubspec_files
from core.file_parsers.rebar_parser import parse_rebar_config_file, parse_rebar_tree_file
from core.file_parsers.rubygem_parser import parse_rubygem_files
from core.file_parsers.sbt_parser import parse_scala_version, parse_build_config_files, \
    construct_tree_file_list, parse_tree_json_file
from core.file_parsers.stack_parser import parse_stack_files, parse_stack_json_file
from core.file_parsers.swift_parser import parse_swift_files
from core.file_parsers.yarn_lock_parser import parse_yarn_lock_file


with open(os.path.join(cf.file_parsers, 'mapper.json'), mode='r', encoding='utf-8') as f:
    mapper = json.load(f)


def get_key(mapper_dict, value):
    return [k for k, v in mapper_dict.items() if value in v]


def update_build_result_by_type(build_result, build_result_by_type):
    if build_result:
        for build_info in build_result:
            if build_info['build_type'] == 'Cpan_Cli' and build_info['build_status'] == 'success' \
                    and build_result_by_type['Cpan_Cli'] == 'failure':
                build_result_by_type.update({'Cpan_Cli': 'success'})
                continue
            elif build_info['build_type'] == 'Go_Mod_Cli' and build_info['build_status'] == 'success' \
                    and build_result_by_type['Go_Mod_Cli'] == 'failure':
                build_result_by_type.update({'Go_Mod_Cli': 'success'})
                continue
            elif build_info['build_type'] == 'Gradle' and build_info['build_status'] == 'success' \
                    and build_result_by_type['Gradle'] == 'failure':
                build_result_by_type.update({'Gradle': 'success'})
                continue
            elif build_info['build_type'] == 'Leiningen' and build_info['build_status'] == 'success' \
                    and build_result_by_type['Leiningen'] == 'failure':
                build_result_by_type.update({'Leiningen': 'success'})
                continue
            elif build_info['build_type'] == 'Maven_Pom' and build_info['build_status'] == 'success' \
                    and build_result_by_type['Maven_Pom'] == 'failure':
                build_result_by_type.update({'Maven_Pom': 'success'})
                continue
            elif build_info['build_type'] == 'Rebar' and build_info['build_status'] == 'success' \
                    and build_result_by_type['Rebar'] == 'failure':
                build_result_by_type.update({'Rebar': 'success'})
                continue
            elif build_info['build_type'] == 'Stack' and build_info['build_status'] == 'success' \
                    and build_result_by_type['Stack'] == 'failure':
                build_result_by_type.update({'Stack': 'success'})
                continue
    return build_result_by_type


def parse_config_files(scan_dir, root_name, is_skip, is_build, build_result, search_result, logger):

    build_result_by_type = {
        'Cpan_Cli': 'failure',
        'Go_Mod_Cli': 'failure',
        'Gradle': 'failure',
        'Leiningen': 'failure',
        'Maven_Pom': 'failure',
        'Rebar': 'failure',
        'Stack': 'failure'
    }
    parse_result = dict()
    cargo_result = list()
    cocoa_result = list()
    composer_result = list()
    conan_result = list()
    cpan_result = list()
    cran_result = list()
    gem_result = list()
    go_result = list()
    hackage_result = list()
    hex_result = list()
    lein_result = list()
    maven_result = list()
    npm_result = list()
    nuget_result = list()
    pub_result = list()
    pypi_result = list()
    swift_result = list()

    scala_version = parse_scala_version(search_result, logger)
    # 非编译构建模式
    if not is_build:
        for file_item in search_result:
            try:
                candidate_keys = get_key(mapper_dict=mapper, value=file_item['file_name'])
                if candidate_keys:
                    if candidate_keys[0] == 'Cargo':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'Cargo.lock')
                        if not os.path.exists(lock_file):
                            logger.info('[+] Start parsing Cargo.toml: ' + file_item['file_path_relative'])
                            dep_result = parse_cargo_files(filepath=file_item['file_path_absolute'], logger=logger)
                            cargo_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing Cargo.lock: ' + lock_file)
                            dep_result = parse_cargo_files(filepath=lock_file, logger=logger)
                            cargo_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Carthage':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'Cartfile.resolved')
                        if not os.path.exists(lock_file):
                            logger.info('[+] Start parsing Cartfile: ' + file_item['file_path_relative'])
                            dep_result = parse_carthage_files(filepath=file_item['file_path_absolute'], logger=logger)
                            cocoa_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing Cartfile.resolved: ' + lock_file)
                            dep_result = parse_carthage_files(filepath=lock_file, logger=logger)
                            cocoa_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Cocoapods':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'Podfile.lock')
                        if not os.path.exists(lock_file):
                            logger.info('[+] Start parsing Podfile: ' + file_item['file_path_relative'])
                            dep_result = parse_cocoa_files(filepath=file_item['file_path_absolute'], logger=logger)
                            cocoa_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing Podfile.lock: ' + lock_file)
                            dep_result = parse_cocoa_files(filepath=lock_file, logger=logger)
                            cocoa_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Composer':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'composer.lock')
                        if not os.path.exists(lock_file):
                            logger.info('[+] Start parsing composer.json: ' + file_item['file_path_relative'])
                            dep_result = parse_composer_files(filepath=file_item['file_path_absolute'], is_skip=is_skip,
                                                              logger=logger)
                            composer_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing composer.lock: ' + lock_file)
                            dep_result = parse_composer_files(filepath=lock_file, is_skip=is_skip, logger=logger)
                            composer_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Conan':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'conan.lock')
                        if os.path.exists(lock_file):
                            logger.info('[+] Start parsing conan.lock: ' + lock_file)
                            dep_result = parse_conan_lock(filepath=lock_file, logger=logger)
                            conan_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Cpan_Deps':
                        logger.info('[+] Start parsing cpanfile: ' + file_item['file_path_relative'])
                        dep_result = parse_cpanfile(filepath=file_item['file_path_absolute'], logger=logger)
                        cpan_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Cran_Deps':
                        logger.info('[+] Start parsing DESCRIPTION: ' + file_item['file_path_relative'])
                        dep_result = parse_cran_files(filepath=file_item['file_path_absolute'], logger=logger)
                        cran_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Dart_Pub':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'pubspec.lock')
                        if not os.path.exists(lock_file):
                            logger.info('[+] Start parsing pubspec.yaml: ' + file_item['file_path_relative'])
                            dep_result = parse_pubspec_files(filepath=file_item['file_path_absolute'], is_skip=is_skip,
                                                             logger=logger)
                            pub_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing pubspec.lock: ' + lock_file)
                            dep_result = parse_pubspec_files(filepath=lock_file, is_skip=is_skip, logger=logger)
                            pub_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Dep':
                        logger.info('[+] Start parsing Gopkg.lock: ' + file_item['file_path_relative'])
                        dep_result = parse_dep_file(filepath=file_item['file_path_absolute'], logger=logger)
                        go_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Gemlock':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'Gemfile.lock')
                        if not os.path.exists(lock_file):
                            logger.info('[+] Start parsing Gemfile: ' + file_item['file_path_relative'])
                            dep_result = parse_rubygem_files(filepath=file_item['file_path_absolute'], logger=logger)
                            gem_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing Gemfile.lock: ' + lock_file)
                            dep_result = parse_gemfile_lock_file(filepath=lock_file, root_name=root_name, logger=logger)
                            gem_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Go_Dep':
                        logger.info('[+] Start parsing Godeps.json: ' + file_item['file_path_relative'])
                        dep_result = parse_godep_file(filepath=file_item['file_path_absolute'], logger=logger)
                        go_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Go_Mod_Cli':
                        sum_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'go.sum')
                        if not os.path.exists(sum_file):
                            logger.info('[+] Start parsing go.mod: ' + file_item['file_path_relative'])
                            dep_result = parse_gomod_files(filepath=file_item['file_path_absolute'], logger=logger)
                            go_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing go.sum: ' + sum_file)
                            dep_result = parse_gomod_files(filepath=sum_file, logger=logger)
                            go_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Leiningen':
                        logger.info('[+] Start parsing project.clj: ' + file_item['file_path_relative'])
                        dep_result = parse_project_clj_file(filepath=file_item['file_path_absolute'], logger=logger)
                        lein_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Maven_Pom':
                        logger.info('[+] Start parsing pom.xml: ' + file_item['file_path_relative'])
                        dep_result = parse_maven_pom_file(filepath=file_item['file_path_absolute'],
                                                          search_result=search_result, logger=logger)
                        maven_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Mix':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'mix.lock')
                        if not os.path.exists(lock_file):
                            logger.info('[+] Start parsing mix.exs: ' + file_item['file_path_relative'])
                            dep_result = parse_mix_files(filepath=file_item['file_path_absolute'], logger=logger)
                            hex_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing mix.lock: ' + lock_file)
                            dep_result = parse_mix_files(filepath=lock_file, logger=logger)
                            hex_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'NPM_Cli':
                        package_lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0],
                                                         'package-lock.json')
                        shrinkwrap_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0],
                                                       'npm-shrinkwrap.json')
                        yarn_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'yarn.lock')
                        pnpm_lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0],
                                                      'pnpm-lock.yaml')
                        if os.path.exists(shrinkwrap_file) or os.path.exists(package_lock_file):
                            if os.path.exists(shrinkwrap_file):
                                logger.info('[+] Start parsing npm-shrinkwrap.json: ' + shrinkwrap_file)
                                dep_result = parse_lock_json_file(filepath=shrinkwrap_file, is_skip=is_skip,
                                                                  logger=logger)
                                npm_result.extend(dep_result)
                                continue
                            elif os.path.exists(package_lock_file):
                                logger.info('[+] Start parsing package-lock.json: ' + package_lock_file)
                                dep_result = parse_lock_json_file(filepath=package_lock_file, is_skip=is_skip,
                                                                  logger=logger)
                                npm_result.extend(dep_result)
                                continue
                        elif os.path.exists(yarn_file):
                            logger.info('[+] Start parsing yarn.lock: ' + yarn_file)
                            dep_result = parse_yarn_lock_file(filepath=yarn_file, logger=logger)
                            npm_result.extend(dep_result)
                            continue
                        elif os.path.exists(pnpm_lock_file):
                            logger.info('[+] Start parsing pnpm-lock.yaml: ' + pnpm_lock_file)
                            dep_result = parse_pnpm_lock_file(filepath=pnpm_lock_file, is_skip=is_skip, logger=logger)
                            npm_result.extend(dep_result)
                            continue
                        else:
                            logger.info('[+] Start parsing package.json: ' + file_item['file_path_relative'])
                            dep_result = parse_package_json_file(filepath=file_item['file_path_absolute'],
                                                                 is_skip=is_skip, logger=logger)
                            npm_result.extend(dep_result)
                            continue
                    elif candidate_keys[0] == 'Nugetconf':
                        logger.info('[+] Start parsing packages.config: ' + file_item['file_path_relative'])
                        dep_result = parse_nuget_files(filepath=file_item['file_path_absolute'], logger=logger)
                        nuget_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Packrat_Lock':
                        logger.info('[+] Start parsing packrat.lock: ' + file_item['file_path_relative'])
                        dep_result = parse_cran_files(filepath=file_item['file_path_absolute'], logger=logger)
                        cran_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Pip_Env':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'Pipfile.lock')
                        if not os.path.exists(lock_file):
                            logger.info('[+] Start parsing Pipfile: ' + file_item['file_path_relative'])
                            dep_result = parse_pipenv_files(filepath=file_item['file_path_absolute'], logger=logger)
                            pypi_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing Pipfile.lock: ' + lock_file)
                            dep_result = parse_pipenv_files(filepath=lock_file, logger=logger)
                            pypi_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Pip_Inspector':
                        logger.info('[+] Start parsing setup.py: ' + file_item['file_path_relative'])
                        dep_result = parse_pip_files(filepath=file_item['file_path_absolute'], logger=logger)
                        pypi_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Poetry':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'poetry.lock')
                        if not os.path.exists(lock_file):
                            logger.info('[+] Start parsing pyproject.toml: ' + file_item['file_path_relative'])
                            dep_result = parse_poetry_files(filepath=file_item['file_path_absolute'], logger=logger)
                            pypi_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing poetry.lock: ' + lock_file)
                            dep_result = parse_poetry_files(filepath=lock_file, logger=logger)
                            pypi_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Rebar':
                        logger.info('[+] Start parsing rebar.config: ' + file_item['file_path_relative'])
                        dep_result = parse_rebar_config_file(filepath=file_item['file_path_absolute'], logger=logger)
                        hex_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Sbt':
                        logger.info('[+] Start parsing build.sbt: ' + file_item['file_path_relative'])
                        dep_result = parse_build_config_files(filepath=file_item['file_path_absolute'],
                                                              scala_version=scala_version, logger=logger)
                        maven_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Swift':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'Package.resolved')
                        if not os.path.exists(lock_file):
                            logger.info('[+] Start parsing Package.swift: ' + file_item['file_path_relative'])
                            dep_result = parse_swift_files(filepath=file_item['file_path_absolute'], logger=logger)
                            swift_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing Package.resolved: ' + lock_file)
                            dep_result = parse_swift_files(filepath=lock_file, logger=logger)
                            swift_result.extend(dep_result)
                        continue
                elif is_podspec_file(filepath=file_item['file_path_absolute']):
                    lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'Podfile.lock')
                    if not os.path.exists(lock_file):
                        logger.info('[+] Start parsing .podspec: ' + file_item['file_path_relative'])
                        dep_result = parse_podspec(filepath=file_item['file_path_absolute'], logger=logger)
                        cocoa_result.extend(dep_result)
                    continue
                elif is_gemspec_file(filepath=file_item['file_path_absolute']):
                    lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'Gemfile.lock')
                    if not os.path.exists(lock_file):
                        logger.info('[+] Start parsing .gemspec: ' + file_item['file_path_relative'])
                        dep_result = parse_rubygem_files(filepath=file_item['file_path_absolute'], logger=logger)
                        gem_result.extend(dep_result)
                    continue
                elif is_build_gradle_file(filepath=file_item['file_path_absolute']):
                    logger.info('[+] Start parsing build.gradle: ' + file_item['file_path_relative'])
                    dep_result = parse_build_gradle_file(filepath=file_item['file_path_absolute'], logger=logger)
                    maven_result.extend(dep_result)
                    continue
                elif is_package_file(filepath=file_item['file_path_absolute']):
                    logger.info('[+] Start parsing package.yaml or *.cabal: ' + file_item['file_path_relative'])
                    dep_result = parse_stack_files(filepath=file_item['file_path_absolute'], logger=logger)
                    hackage_result.extend(dep_result)
                    continue
                elif is_project_file(filepath=file_item['file_path_absolute']):
                    config_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'packages.config')
                    if not os.path.exists(config_file):
                        logger.info('[+] Start parsing .csproj or .nuspec: ' + file_item['file_path_relative'])
                        dep_result = parse_nuget_files(filepath=file_item['file_path_absolute'], logger=logger)
                        nuget_result.extend(dep_result)
                    continue
                elif is_requirements_file(filepath=file_item['file_path_absolute']):
                    logger.info('[+] Start parsing requirements.txt: ' + file_item['file_path_relative'])
                    dep_result = parse_pip_files(filepath=file_item['file_path_absolute'], logger=logger)
                    pypi_result.extend(dep_result)
                    continue
                elif is_environment_file(filepath=file_item['file_path_absolute']):
                    logger.info('[+] Start parsing environment.yml: ' + file_item['file_path_relative'])
                    dep_result = parse_environment_file(filepath=file_item['file_path_absolute'], logger=logger)
                    pypi_result.extend(dep_result)
                    continue
                elif is_dependencies_scala_file(filepath=file_item['file_path_absolute']):
                    logger.info('[+] Start parsing dependencies.scala: ' + file_item['file_path_relative'])
                    dep_result = parse_build_config_files(filepath=file_item['file_path_absolute'],
                                                          scala_version=scala_version, logger=logger)
                    maven_result.extend(dep_result)
                    continue
            except Exception as e:
                logger.error('Exception occurs when parsing config file {}: {}'.format(file_item['file_path_absolute'],
                                                                                       str(e)))
                continue

    # 编译构建模式
    else:
        build_result_by_type = update_build_result_by_type(build_result=build_result,
                                                           build_result_by_type=build_result_by_type)

        for file_item in search_result:
            try:
                candidate_keys = get_key(mapper_dict=mapper, value=file_item['file_name'])
                if candidate_keys:
                    if candidate_keys[0] == 'Cargo':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'Cargo.lock')
                        if not os.path.exists(lock_file):
                            logger.info('[+] Start parsing Cargo.toml: ' + file_item['file_path_relative'])
                            dep_result = parse_cargo_files(filepath=file_item['file_path_absolute'], logger=logger)
                            cargo_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing Cargo.lock: ' + lock_file)
                            dep_result = parse_cargo_files(filepath=lock_file, logger=logger)
                            cargo_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Carthage':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'Cartfile.resolved')
                        if not os.path.exists(lock_file):
                            logger.info('[+] Start parsing Cartfile: ' + file_item['file_path_relative'])
                            dep_result = parse_carthage_files(filepath=file_item['file_path_absolute'], logger=logger)
                            cocoa_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing Cartfile.resolved: ' + lock_file)
                            dep_result = parse_carthage_files(filepath=lock_file, logger=logger)
                            cocoa_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Cocoapods':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'Podfile.lock')
                        if not os.path.exists(lock_file):
                            logger.info('[+] Start parsing Podfile: ' + file_item['file_path_relative'])
                            dep_result = parse_cocoa_files(filepath=file_item['file_path_absolute'], logger=logger)
                            cocoa_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing Podfile.lock: ' + lock_file)
                            dep_result = parse_cocoa_files(filepath=lock_file, logger=logger)
                            cocoa_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Composer':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'composer.lock')
                        if not os.path.exists(lock_file):
                            logger.info('[+] Start parsing composer.json: ' + file_item['file_path_relative'])
                            dep_result = parse_composer_files(filepath=file_item['file_path_absolute'], is_skip=is_skip,
                                                              logger=logger)
                            composer_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing composer.lock: ' + lock_file)
                            dep_result = parse_composer_files(filepath=lock_file, is_skip=is_skip, logger=logger)
                            composer_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Conan':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'conan.lock')
                        if os.path.exists(lock_file):
                            logger.info('[+] Start parsing conan.lock: ' + lock_file)
                            dep_result = parse_conan_lock(filepath=lock_file, logger=logger)
                            conan_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Cpan_Cli':
                        if build_result_by_type['Cpan_Cli'] == 'success':
                            dep_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'cpan_deps.txt')
                            if os.path.exists(dep_file):
                                logger.info('[+] Start parsing cpan_deps.txt: ' + dep_file)
                                dep_result = parse_cpandeps(filepath=dep_file, logger=logger)
                                cpan_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Cpan_Deps':
                        if build_result_by_type['Cpan_Cli'] == 'failure':
                            logger.info('[+] Start parsing cpanfile: ' + file_item['file_path_relative'])
                            dep_result = parse_cpanfile(filepath=file_item['file_path_absolute'], logger=logger)
                            cpan_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Cran_Deps':
                        logger.info('[+] Start parsing DESCRIPTION: ' + file_item['file_path_relative'])
                        dep_result = parse_cran_files(filepath=file_item['file_path_absolute'], logger=logger)
                        cran_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Dart_Pub':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'pubspec.lock')
                        if not os.path.exists(lock_file):
                            logger.info('[+] Start parsing pubspec.yaml: ' + file_item['file_path_relative'])
                            dep_result = parse_pubspec_files(filepath=file_item['file_path_absolute'], is_skip=is_skip,
                                                             logger=logger)
                            pub_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing pubspec.lock: ' + lock_file)
                            dep_result = parse_pubspec_files(filepath=lock_file, is_skip=is_skip, logger=logger)
                            pub_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Dep':
                        logger.info('[+] Start parsing Gopkg.lock: ' + file_item['file_path_relative'])
                        dep_result = parse_dep_file(filepath=file_item['file_path_absolute'], logger=logger)
                        go_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Gemlock':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'Gemfile.lock')
                        if not os.path.exists(lock_file):
                            logger.info('[+] Start parsing Gemfile: ' + file_item['file_path_relative'])
                            dep_result = parse_rubygem_files(filepath=file_item['file_path_absolute'], logger=logger)
                            gem_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing Gemfile.lock: ' + lock_file)
                            dep_result = parse_gemfile_lock_file(filepath=lock_file, root_name=root_name, logger=logger)
                            gem_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Go_Dep':
                        logger.info('[+] Start parsing Godeps.json: ' + file_item['file_path_relative'])
                        dep_result = parse_godep_file(filepath=file_item['file_path_absolute'], logger=logger)
                        go_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Go_Mod_Cli':
                        if build_result_by_type['Go_Mod_Cli'] == 'success':
                            list_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0],
                                                     'gomod_list.txt')
                            if os.path.exists(list_file):
                                logger.info('[+] Starting parsing gomod_list.txt: ' + list_file)
                                dep_result = parse_gomod_list_file(filepath=list_file, logger=logger)
                                go_result.extend(dep_result)
                        else:
                            sum_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'go.sum')
                            if not os.path.exists(sum_file):
                                logger.info('[+] Start parsing go.mod: ' + file_item['file_path_relative'])
                                dep_result = parse_gomod_files(filepath=file_item['file_path_absolute'], logger=logger)
                                go_result.extend(dep_result)
                            else:
                                logger.info('[+] Start parsing go.sum: ' + sum_file)
                                dep_result = parse_gomod_files(filepath=sum_file, logger=logger)
                                go_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Leiningen':
                        if build_result_by_type['Leiningen'] == 'success':
                            tree_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'lein_maven_tree.txt')
                            if os.path.exists(tree_file):
                                logger.info('[+] Starting parsing lein_maven_tree.txt: ' + tree_file)
                                dep_result = parse_lein_tree_file(filepath=tree_file, logger=logger)
                                lein_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing project.clj: ' + file_item['file_path_relative'])
                            dep_result = parse_project_clj_file(filepath=file_item['file_path_absolute'], logger=logger)
                            lein_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Maven_Pom':
                        if build_result_by_type['Maven_Pom'] == 'success':
                            tree_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'maven_tree.txt')
                            if os.path.exists(tree_file):
                                logger.info('[+] Starting parsing maven_tree.txt: ' + tree_file)
                                dep_result = parse_maven_tree_file(filepath=tree_file, logger=logger)
                                maven_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing pom.xml: ' + file_item['file_path_relative'])
                            dep_result = parse_maven_pom_file(filepath=file_item['file_path_absolute'],
                                                              search_result=search_result, logger=logger)
                            maven_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Mix':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'mix.lock')
                        if not os.path.exists(lock_file):
                            logger.info('[+] Start parsing mix.exs: ' + file_item['file_path_relative'])
                            dep_result = parse_mix_files(filepath=file_item['file_path_absolute'], logger=logger)
                            hex_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing mix.lock: ' + lock_file)
                            dep_result = parse_mix_files(filepath=lock_file, logger=logger)
                            hex_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'NPM_Cli':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'package-lock.json')
                        if os.path.exists(lock_file):
                            logger.info('[+] Start parsing package-lock.json: ' + lock_file)
                            dep_result = parse_lock_json_file(filepath=lock_file, is_skip=is_skip, logger=logger)
                            npm_result.extend(dep_result)
                            continue
                        else:
                            yarn_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'yarn.lock')
                            pnpm_lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0],
                                                          'pnpm-lock.yaml')
                            if os.path.exists(yarn_file):
                                logger.info('[+] Start parsing yarn.lock: ' + yarn_file)
                                dep_result = parse_yarn_lock_file(filepath=yarn_file, logger=logger)
                                npm_result.extend(dep_result)
                                continue
                            elif os.path.exists(pnpm_lock_file):
                                logger.info('[+] Start parsing pnpm-lock.yaml: ' + pnpm_lock_file)
                                dep_result = parse_pnpm_lock_file(filepath=pnpm_lock_file, is_skip=is_skip,
                                                                  logger=logger)
                                npm_result.extend(dep_result)
                                continue
                            else:
                                logger.info('[+] Start parsing package.json: ' + file_item['file_path_relative'])
                                dep_result = parse_package_json_file(filepath=file_item['file_path_absolute'],
                                                                     is_skip=is_skip, logger=logger)
                                npm_result.extend(dep_result)
                                continue
                    elif candidate_keys[0] == 'Nugetconf':
                        logger.info('[+] Start parsing packages.config: ' + file_item['file_path_relative'])
                        dep_result = parse_nuget_files(filepath=file_item['file_path_absolute'], logger=logger)
                        nuget_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Packrat_Lock':
                        logger.info('[+] Start parsing packrat.lock: ' + file_item['file_path_relative'])
                        dep_result = parse_cran_files(filepath=file_item['file_path_absolute'], logger=logger)
                        cran_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Pip_Env':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'Pipfile.lock')
                        if not os.path.exists(lock_file):
                            logger.info('[+] Start parsing Pipfile: ' + file_item['file_path_relative'])
                            dep_result = parse_pipenv_files(filepath=file_item['file_path_absolute'], logger=logger)
                            pypi_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing Pipfile.lock: ' + lock_file)
                            dep_result = parse_pipenv_files(filepath=lock_file, logger=logger)
                            pypi_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Pip_Inspector':
                        logger.info('[+] Start parsing setup.py: ' + file_item['file_path_relative'])
                        dep_result = parse_pip_files(filepath=file_item['file_path_absolute'], logger=logger)
                        pypi_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Poetry':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'poetry.lock')
                        if not os.path.exists(lock_file):
                            logger.info('[+] Start parsing pyproject.toml: ' + file_item['file_path_relative'])
                            dep_result = parse_poetry_files(filepath=file_item['file_path_absolute'], logger=logger)
                            pypi_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing poetry.lock: ' + lock_file)
                            dep_result = parse_poetry_files(filepath=lock_file, logger=logger)
                            pypi_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Rebar':
                        if build_result_by_type['Rebar'] == 'success':
                            tree_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'rebar_tree.txt')
                            if os.path.exists(tree_file):
                                logger.info('[+] Starting parsing rebar_tree.txt: ' + tree_file)
                                dep_result = parse_rebar_tree_file(filepath=tree_file, logger=logger)
                                hex_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing rebar.config: ' + file_item['file_path_relative'])
                            dep_result = parse_rebar_config_file(filepath=file_item['file_path_absolute'],
                                                                 logger=logger)
                            hex_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Sbt':
                        filepath_list = construct_tree_file_list(scan_dir=scan_dir)
                        if filepath_list:
                            dep_result = parse_tree_json_file(root_name=root_name, filepath_list=filepath_list,
                                                              logger=logger)
                            maven_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing build.sbt: ' + file_item['file_path_relative'])
                            dep_result = parse_build_config_files(filepath=file_item['file_path_absolute'],
                                                                  scala_version=scala_version, logger=logger)
                            maven_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Stack':
                        if build_result_by_type['Stack'] == 'success':
                            json_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'stack_deps.json')
                            if os.path.exists(json_file):
                                logger.info('[+] Starting parsing stack_deps.json: ' + json_file)
                                dep_result = parse_stack_json_file(filepath=json_file, logger=logger)
                                hackage_result.extend(dep_result)
                        continue
                    elif candidate_keys[0] == 'Swift':
                        lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'Package.resolved')
                        if not os.path.exists(lock_file):
                            logger.info('[+] Start parsing Package.swift: ' + file_item['file_path_relative'])
                            dep_result = parse_swift_files(filepath=file_item['file_path_absolute'], logger=logger)
                            swift_result.extend(dep_result)
                        else:
                            logger.info('[+] Start parsing Package.resolved: ' + lock_file)
                            dep_result = parse_swift_files(filepath=lock_file, logger=logger)
                            swift_result.extend(dep_result)
                        continue
                elif is_podspec_file(filepath=file_item['file_path_absolute']):
                    lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'Podfile.lock')
                    if not os.path.exists(lock_file):
                        logger.info('[+] Start parsing .podspec: ' + file_item['file_path_relative'])
                        dep_result = parse_podspec(filepath=file_item['file_path_absolute'], logger=logger)
                        cocoa_result.extend(dep_result)
                    continue
                elif is_gemspec_file(filepath=file_item['file_path_absolute']):
                    lock_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'Gemfile.lock')
                    if not os.path.exists(lock_file):
                        logger.info('[+] Start parsing .gemspec: ' + file_item['file_path_relative'])
                        dep_result = parse_rubygem_files(filepath=file_item['file_path_absolute'], logger=logger)
                        gem_result.extend(dep_result)
                    continue
                elif is_build_gradle_file(filepath=file_item['file_path_absolute']):
                    if build_result_by_type['Gradle'] == 'success':
                        tree_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'gradle_tree.txt')
                        if os.path.exists(tree_file):
                            logger.info('[+] Start parsing gradle_tree.txt: ' + tree_file)
                            dep_result = parse_gradle_tree_file(filepath=tree_file, logger=logger)
                            maven_result.extend(dep_result)
                    else:
                        logger.info('[+] Start parsing build.gradle: ' + file_item['file_path_relative'])
                        dep_result = parse_build_gradle_file(filepath=file_item['file_path_absolute'], logger=logger)
                        maven_result.extend(dep_result)
                    continue
                elif is_package_file(filepath=file_item['file_path_absolute']):
                    if build_result_by_type['Stack'] == 'failure':
                        logger.info('[+] Start parsing package.yaml or *.cabal: ' + file_item['file_path_relative'])
                        dep_result = parse_stack_files(filepath=file_item['file_path_absolute'], logger=logger)
                        hackage_result.extend(dep_result)
                    continue
                elif is_project_file(filepath=file_item['file_path_absolute']):
                    config_file = os.path.join(os.path.split(file_item['file_path_absolute'])[0], 'packages.config')
                    if not os.path.exists(config_file):
                        logger.info('[+] Start parsing .csproj or .nuspec: ' + file_item['file_path_relative'])
                        dep_result = parse_nuget_files(filepath=file_item['file_path_absolute'], logger=logger)
                        nuget_result.extend(dep_result)
                    continue
                elif is_requirements_file(filepath=file_item['file_path_absolute']):
                    logger.info('[+] Start parsing requirements.txt: ' + file_item['file_path_relative'])
                    dep_result = parse_pip_files(filepath=file_item['file_path_absolute'], logger=logger)
                    pypi_result.extend(dep_result)
                    continue
                elif is_environment_file(filepath=file_item['file_path_absolute']):
                    logger.info('[+] Start parsing environment.yml: ' + file_item['file_path_relative'])
                    dep_result = parse_environment_file(filepath=file_item['file_path_absolute'], logger=logger)
                    pypi_result.extend(dep_result)
                    continue
                elif is_dependencies_scala_file(filepath=file_item['file_path_absolute']):
                    # TODO: 能否少获取一次tree_file_list
                    filepath_list = construct_tree_file_list(scan_dir=scan_dir)
                    if not filepath_list:
                        logger.info('[+] Start parsing dependencies.scala: ' + file_item['file_path_relative'])
                        dep_result = parse_build_config_files(filepath=file_item['file_path_absolute'],
                                                              scala_version=scala_version, logger=logger)
                        maven_result.extend(dep_result)
                    continue
            except Exception as e:
                logger.error('Exception occurs when parsing config file {}: {}'.format(file_item['file_path_absolute'],
                                                                                       str(e)))
                continue

    try:
        parse_result['cargo_result'] = remove_duplicate_dict_items(data_list=cargo_result)
        parse_result['cocoa_result'] = remove_duplicate_dict_items(data_list=cocoa_result)
        parse_result['composer_result'] = remove_duplicate_dict_items(data_list=composer_result)
        parse_result['conan_result'] = remove_duplicate_dict_items(data_list=conan_result)
        parse_result['cpan_result'] = remove_duplicate_dict_items(data_list=cpan_result)
        parse_result['cran_result'] = remove_duplicate_dict_items(data_list=cran_result)
        parse_result['gem_result'] = remove_duplicate_dict_items(data_list=gem_result)
        parse_result['go_result'] = remove_duplicate_dict_items(data_list=go_result)
        parse_result['hackage_result'] = remove_duplicate_dict_items(data_list=hackage_result)
        parse_result['hex_result'] = remove_duplicate_dict_items(data_list=hex_result)
        parse_result['lein_result'] = remove_duplicate_dict_items(data_list=lein_result)
        parse_result['maven_result'] = remove_duplicate_dict_items(data_list=maven_result)
        parse_result['npm_result'] = remove_duplicate_dict_items(data_list=npm_result)
        parse_result['nuget_result'] = remove_duplicate_dict_items(data_list=nuget_result)
        parse_result['pub_result'] = remove_duplicate_dict_items(data_list=pub_result)
        parse_result['pypi_result'] = remove_duplicate_dict_items(data_list=pypi_result)
        parse_result['swift_result'] = remove_duplicate_dict_items(data_list=swift_result)
    except Exception as e:
        logger.error('Exception occurs in function remove_duplicate_dict_items when adding dep_items to parse_result: '
                     '{}'.format(str(e)))

    return parse_result
