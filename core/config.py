import os
import sys

# 根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 配置文件列表
CANDIDATE_FILE_LIST = ['Cargo.toml', 'Cartfile', 'Podfile', 'composer.json', 'conanfile.py', 'Makefile.PL', 'Build.PL',
                       'cpanfile', 'DESCRIPTION', 'pubspec.yaml', 'Gopkg.lock', 'Gemfile', 'Godeps.json', 'go.mod',
                       'project.clj', 'pom.xml', 'mix.exs', 'package.json', 'packages.config', 'packrat.lock',
                       'Pipfile', 'setup.py', 'pyproject.toml', 'rebar.config', 'build.sbt', 'stack.yaml', 'Package.swift']


class Config(object):

    scanning_dir = os.path.join(BASE_DIR, 'core')
    log_dir = os.path.join(BASE_DIR, 'log_dir')
    temp_dir = os.path.join(BASE_DIR, 'temp_dir')
    executables = os.path.join(BASE_DIR, 'core', 'executables')
    file_parsers = os.path.join(BASE_DIR, 'core', 'file_parsers')

    is_build = False
    is_skip = False
    search_depth = 3
    is_output = False
    output_dir = '../check_result'


if __name__ == "__main__":
    print(sys.platform)
    print(len(CANDIDATE_FILE_LIST))
