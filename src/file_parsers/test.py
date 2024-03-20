import os
import json
import subprocess
import statistics
import logging
from core.log import Logger
from core.parse import parse_temp_file
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
from core.file_parsers.sbt_parser import parse_build_config_files, construct_tree_file_list, parse_tree_json_file
from core.file_parsers.stack_parser import parse_stack_files, parse_stack_json_file
from core.file_parsers.swift_parser import parse_swift_files
from core.file_parsers.yarn_lock_parser import parse_yarn_lock_file


def tool_check(tool_dir, temp_filepath, scan_dir):
    command = tool_dir + " --out " + temp_filepath + " --scan " + scan_dir + \
              " --format JSON --enableExperimental --noupdate" \
              " --disableOssIndex --disableOssIndexCache --disableRetireJS" \
              " --disableNodeAudit --disableNodeAuditCache --disablePnpmAudit --disableYarnAudit"
    command_params = command.split()
    p = subprocess.Popen(command_params, shell=False)
    p.communicate()
    returncode = p.returncode
    if returncode == 0:
        return temp_filepath
    if returncode != 0:
        if os.path.exists(temp_filepath):
            return temp_filepath
        else:
            return None


def calculate(build_filepath, buildless_filepath):
    ns = {
        'Erlang': '/',
        'Golang': '/',
        'Perl': '::',
        'Swift': '/'
    }
    count = 0

    with open(build_filepath, mode='r', encoding='utf-8') as f:
        build_result_data = json.load(f)
    with open(buildless_filepath, mode='r', encoding='utf-8') as f:
        buildless_result_data = json.load(f)

    build_deps = build_result_data['dep_result']
    build_deps_names = list()
    for build_dep in build_deps:
        if build_dep['name'] not in build_deps_names:
            if build_dep['language'] == 'Erlang' and build_dep['namespace']:
                build_deps_names.append(build_dep['namespace'] + ns['Erlang'] + build_dep['name'])
            elif build_dep['language'] == 'Golang' and build_dep['namespace']:
                build_deps_names.append(build_dep['namespace'] + ns['Golang'] + build_dep['name'])
            elif build_dep['language'] == 'Perl' and build_dep['namespace']:
                build_deps_names.append(build_dep['namespace'] + ns['Perl'] + build_dep['name'])
            elif build_dep['language'] == 'Swift' and build_dep['namespace']:
                build_deps_names.append(build_dep['namespace'] + ns['Swift'] + build_dep['name'])
            else:
                build_deps_names.append(build_dep['name'])
    build_deps_names_nums = len(build_deps_names)

    buildless_deps = buildless_result_data['dep_result']
    buildless_deps_names = list()
    for buildless_dep in buildless_deps:
        if buildless_dep['name'] not in buildless_deps_names:
            if buildless_dep['language'] == 'Erlang' and buildless_dep['namespace']:
                buildless_deps_names.append(buildless_dep['namespace'] + ns['Erlang'] + buildless_dep['name'])
            elif buildless_dep['language'] == 'Golang' and buildless_dep['namespace']:
                buildless_deps_names.append(buildless_dep['namespace'] + ns['Golang'] + buildless_dep['name'])
            elif buildless_dep['language'] == 'Perl' and buildless_dep['namespace']:
                buildless_deps_names.append(buildless_dep['namespace'] + ns['Perl'] + buildless_dep['name'])
            elif buildless_dep['language'] == 'Swift' and buildless_dep['namespace']:
                buildless_deps_names.append(buildless_dep['namespace'] + ns['Swift'] + buildless_dep['name'])
            else:
                buildless_deps_names.append(buildless_dep['name'])
    buildless_deps_names_nums = len(buildless_deps_names)

    for buildless_deps_name in buildless_deps_names:
        if buildless_deps_name in build_deps_names:
            count = count + 1

    return buildless_deps_names_nums, build_deps_names_nums, count


if __name__ == "__main__":

    # 检测结果个数统计
    # _list = os.walk('../../evaluation/check_result')
    # count_all = 0
    # count = 0
    # for root, _, files in _list:
    #     for file in files:
    #         if 'buildless' in file:
    #             filepath = os.path.join(root, file)
    #             with open(filepath, mode='r', encoding='utf-8') as f:
    #                 dep_num = json.load(f)['dep_nums']
    #                 count_all = count_all + int(dep_num)
    #                 if dep_num < 100:
    #                     count = count + int(dep_num)
    # print(count_all)
    # print(count)

    # 非编译检测结果 vs 编译检测结果
    project_name_list = ['absinthe', 'annotate_gem', 'App-perlbrew', 'appraisal', 'axios-0.19.2', 'bfg-repo-cleaner',
                         'cargo-expand', 'cargo-generate', 'cargo-update', 'clojurescript', 'compojure',
                         'composer-cleaner', 'connectanum-dart', 'cookie-parser-1.4.5', 'cowboy',
                         'cyclonedx-maven-plugin', 'discord-haskell', 'erldns', 'es6-promise-4.2.8', 'flex',
                         'flutter_map', 'gradle-download-task', 'hackney', 'hadolint', 'hlint', 'image',
                         'integration-common', 'cli-1.22.4', 'mall', 'Perl-Critic', 'PHPMailer', 'quantum-core',
                         'redigo-1.8.2', 'redis-7.2.0', 'scalacheck', 'swift-math-parser', 'TextBuilder',
                         'weixin-java-mp-demo']
    res_list_1 = list()
    res_list_2 = list()
    for project_name in project_name_list:
        build_filepath = '../../evaluation/check_result/' + 'dep-check__' + project_name + '__build.json'
        buildless_filepath = '../../evaluation/check_result/' + 'dep-check__' + project_name + '__buildless.json'
        buildless_deps_names_nums, build_deps_names_nums, count = calculate(build_filepath, buildless_filepath)
        print('项目名称：' + project_name)
        print('非编译依赖项个数：', str(buildless_deps_names_nums))
        print('编译依赖项个数：', str(build_deps_names_nums))
        print('非编译依赖项在编译依赖项中的个数：' + str(count))
        print('在非编译依赖项总数中的占比：' + str(round(count/buildless_deps_names_nums, 2)))
        res_list_1.append(round(count/buildless_deps_names_nums, 2))
        transitive_nums = build_deps_names_nums - count
        if transitive_nums > 0:
            transitive_prop = round(transitive_nums/build_deps_names_nums, 2)
        else:
            transitive_prop = 0
        print('传递依赖项在编译依赖项中的个数：' + str(transitive_nums))
        print('传递依赖项在编译依赖项中的占比：' + str(transitive_prop))
        res_list_2.append(transitive_prop)
        print('-----------------------------------')
    print(statistics.mean(res_list_1))
    print(statistics.mean(res_list_2))

    # 非编译检测结果 vs 非编译人工提取结果
    # log = Logger(path='../../log_dir/test.log', cmd_level=logging.INFO, file_level=logging.ERROR)
    # dep_result = list()
    #
    # file_list = [
    #     '/Users/rongdang/Desktop/sca-2.0/extracted_folder/golang/cli-1.22.4/go.sum'
    # ]
    # search_result = []
    #
    # print('file: ')
    # for file in file_list:
    #     print(file)
    #     res = parse_gomod_files(filepath=file, logger=log)
    #     dep_result.extend(res)
    # dep_result = remove_duplicate_dict_items(data_list=dep_result)
    # if dep_result:
    #     print('nums: ' + str(len(dep_result)))
    #     for item in dep_result:
    #         print(item)

    # 检测结果 vs dependency-check检测结果
    # tool_dir = '../dependency-check/bin/dependency-check.sh'
    # project_path_list = [
    #     'c#/NugetUpdater', 'c#/pkgdiff', 'c#/QuickOpcPackagesConfig',
    #     'dart/connectanum-dart', 'dart/flutter_map', 'dart/image',
    #     'golang/cli-1.22.4', 'golang/redigo-1.8.2', 'golang/redis-7.2.0',
    #     'javascript/axios-0.19.2', 'javascript/cookie-parser-1.4.5', 'javascript/es6-promise-4.2.8',
    #     'objective_c/fmdb', 'objective_c/VulnerablePodfile', 'perl/App-perlbrew', 'perl/Perl-Critic',
    #     'python/kornia', 'python/learning-real-bug-detector', 'python/probabilistic-forecasts-attacks',
    #     'ruby/annotate_gem', 'ruby/appraisal', 'ruby/gem_updater', 'swift/swift-math-parser', 'swift/TextBuilder'
    # ]
    # for project_path in project_path_list:
    #     scan_dir = '../../extracted_folder/' + project_path
    #     project_name = scan_dir.split('/')[-1]
    #     result_filepath = '../../evaluation/tool_check_result/tool-check__' + project_name + '.json'
    #
    #     temp_filepath = '../../temp_dir/' + project_name + '.json'
    #     temp_json_path = tool_check(tool_dir, temp_filepath, scan_dir)
    #     if temp_json_path:
    #         dep_result_dict = parse_temp_file(temp_file_path=temp_json_path, logger=log)
    #         dep_result_list = list()
    #         for _, dep_result in dep_result_dict.items():
    #             dep_result_list.append(dep_result)
    #         dep_result_list = remove_duplicate_dict_items(data_list=dep_result_list)
    #         data = {
    #             'dep_nums': len(dep_result_list) if dep_result_list else 0,
    #             'dep_result': dep_result_list if dep_result_list else list()
    #         }
    #         print('start writing result: ' + project_name)
    #         with open(result_filepath, mode='w', encoding='utf-8') as json_file_to_write:
    #             json_file_to_write.write(json.dumps(data, indent=4))
    #         json_file_to_write.close()
