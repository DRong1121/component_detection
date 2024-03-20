#
# Copyright (c) nexB Inc. and others. All rights reserved.
# ScanCode is a trademark of nexB Inc.
# SPDX-License-Identifier: Apache-2.0
# See http://www.apache.org/licenses/LICENSE-2.0 for the license text.
# See https://github.com/nexB/scancode-toolkit for support or download.
# See https://aboutcode.org for more information about nexB OSS projects.
#
from pygmars import Token
from pygmars.parse import Parser
from pygments import lex

from core.file_parsers.groovy_lexer import GroovyLexer
from core.util import remove_duplicate_dict_items


grammar = """
    LIT-STRING: {<LITERAL-STRING-SINGLE|LITERAL-STRING-DOUBLE>}
    PACKAGE-IDENTIFIER: {<OPERATOR> <TEXT>? <NAME-LABEL> <TEXT>? <LIT-STRING>}
    DEPENDENCY-1: {<PACKAGE-IDENTIFIER>{3} <OPERATOR>}
    DEPENDENCY-2: {<NAME> <TEXT> <LIT-STRING> <TEXT>}
    DEPENDENCY-3: {<NAME> <TEXT>? <OPERATOR> <LIT-STRING> <OPERATOR>}
    DEPENDENCY-4: {<NAME> <TEXT> <NAME-LABEL> <TEXT> <LIT-STRING> <PACKAGE-IDENTIFIER> <PACKAGE-IDENTIFIER> <OPERATOR>? <TEXT>}
    DEPENDENCY-5: {<NAME> <TEXT> <NAME> <OPERATOR> <NAME-ATTRIBUTE>}
    NESTED-DEPENDENCY-1: {<NAME> <OPERATOR> <DEPENDENCY-1>+ }
"""


def get_tokens(contents):
    """
    Yield tuples of (position, Token, value) from lexing a ``contents`` string.
    """
    for i, (token, value) in enumerate(lex(contents, GroovyLexer())):
        yield i, token, value


def get_pygmar_tokens(contents):
    tokens = Token.from_pygments_tokens(get_tokens(contents))
    for token in tokens:
        if token.label == 'NAME' and token.value == 'dependencies':
            token.label = 'DEPENDENCIES-START'
        yield token


def is_literal_string(string):
    return string in ('LITERAL-STRING-SINGLE', 'LITERAL-STRING-DOUBLE')


def remove_quotes(string):
    """
    Remove starting and ending quotes from ``string``.
    If ``string`` has no starting or ending quotes, return ``string``.
    """
    quoted = lambda x: (
        (x.startswith('"') and x.endswith('"'))
        or (x.startswith("'") and x.endswith("'"))
    )
    if quoted:
        return string[1:-1]
    else:
        return string


def parse_version_str(version_str):
    # TODO: parse semantic version string
    if version_str.startswith('$'):
        version_str = ''
    elif version_str.endswith('!!'):
        version_str = version_str.replace('!!', '')
    elif version_str.endswith('+'):
        lower = version_str.replace('+', '0')
        nums = lower.split('.')
        nums[0] = str(int(nums[0]) + 1)
        upper = '.'.join(nums)
        version_str = '>=' + lower + ', <' + upper
    return version_str


def parse_build_gradle_file(filepath, logger):
    """
    Return dependency items based on parse tree.
    """
    dependencies = list()
    in_dependency_block = False
    brackets_counter = 0
    first_bracket_seen = False

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            contents = file.read()

        parser = Parser(grammar)
        lexed_tokens = list(get_pygmar_tokens(contents))
        parse_tree = parser.parse(lexed_tokens)

    except Exception as e:
        logger.error('Exception occurs when loading build.gradle file {}: {}'.format(filepath, str(e)))
        return dependencies

    if parse_tree:
        # print(parse_tree)
        for tree_node in parse_tree:
            if tree_node.label == 'DEPENDENCIES-START':
                in_dependency_block = True
                continue

            if in_dependency_block:
                if tree_node.label.startswith('OPERATOR'):
                    if tree_node.value == '{':
                        if not first_bracket_seen:
                            first_bracket_seen = True
                        brackets_counter += 1
                    elif tree_node.value == '}':
                        brackets_counter -= 1

                    if brackets_counter == 0 and first_bracket_seen:
                        in_dependency_block = False
                        continue

                # NESTED DEPENDENCY 1
                if tree_node.label == 'NESTED-DEPENDENCY-1':
                    dependency = {}
                    last_key = None
                    for child_node in tree_node.leaves():
                        if child_node.label == 'NAME-LABEL':
                            value = child_node.value
                            if value == 'group:':
                                last_key = 'namespace'
                            if value == 'name:':
                                last_key = 'name'
                            if value == 'version:':
                                last_key = 'version'

                        if is_literal_string(child_node.label):
                            if last_key == 'version':
                                try:
                                    dependency[last_key] = parse_version_str(remove_quotes(child_node.value))
                                except Exception as e:
                                    logger.error(
                                        'Exception occurs in function parse_version_str '
                                        'when parsing build.gradle on {}: {}'.format(filepath, str(e)))
                                    dependency[last_key] = ''
                            else:
                                dependency[last_key] = remove_quotes(child_node.value)

                    if dependency and dependency['namespace']:
                        dependency['name'] = dependency['namespace'] + '/' + dependency['name']
                        dependency['type'] = 'maven'
                        dependency['language'] = 'Java'
                        dependencies.append(dependency)

                # DEPENDENCY 1-5
                if tree_node.label == 'DEPENDENCY-1':
                    name_label_to_dep_field_name = {
                        'group:': 'namespace',
                        'name:': 'name',
                        'version:': 'version'
                    }
                    dependency = {}
                    last_key = None
                    for child_node in tree_node.leaves():
                        value = child_node.value
                        if child_node.label == 'NAME-LABEL':
                            last_key = name_label_to_dep_field_name.get(value, '')
                        if is_literal_string(child_node.label):
                            if last_key:
                                if last_key == 'version':
                                    try:
                                        dependency[last_key] = parse_version_str(remove_quotes(value))
                                    except Exception as e:
                                        logger.error(
                                            'Exception occurs in function parse_version_str '
                                            'when parsing build.gradle on {}: {}'.format(filepath, str(e)))
                                        dependency[last_key] = ''
                                else:
                                    dependency[last_key] = remove_quotes(value)

                    if dependency and dependency['namespace']:
                        dependency['name'] = dependency['namespace'] + '/' + dependency['name']
                        dependency['type'] = 'maven'
                        dependency['language'] = 'Java'
                        dependencies.append(dependency)

                if tree_node.label == 'DEPENDENCY-2':
                    dependency = {}
                    for child_node in tree_node.leaves():
                        if is_literal_string(child_node.label):
                            value = child_node.value
                            value = remove_quotes(value)

                            namespace = ''
                            name = ''
                            version = ''
                            split_value = value.split(':')
                            split_value_length = len(split_value)
                            if split_value_length == 4:
                                # We are assuming `value` is in the form of "namespace:name:version:module"
                                # We are currently not reporting down to the module level
                                namespace, name, version, _ = split_value
                            if split_value_length == 3:
                                # We are assuming `value` is in the form of "namespace:name:version"
                                namespace, name, version = split_value
                            if split_value_length == 2:
                                # We are assuming `value` is in the form of "namespace:name"
                                namespace, name = split_value

                            dependency['namespace'] = namespace
                            dependency['name'] = name
                            try:
                                dependency['version'] = parse_version_str(version)
                            except Exception as e:
                                logger.error(
                                    'Exception occurs in function parse_version_str '
                                    'when parsing build.gradle on {}: {}'.format(filepath, str(e)))
                                dependency['version'] = ''

                    if dependency and dependency['namespace']:
                        if dependency['namespace'] == 'pypi':
                            dependency['namespace'] = ''
                            dependency['type'] = 'pypi'
                            dependency['language'] = 'Python'
                        else:
                            dependency['name'] = dependency['namespace'] + '/' + dependency['name']
                            dependency['type'] = 'maven'
                            dependency['language'] = 'Java'
                        dependencies.append(dependency)

                if tree_node.label == 'DEPENDENCY-3':
                    dependency = {}
                    for child_node in tree_node.leaves():
                        if is_literal_string(child_node.label):

                            value = child_node.value
                            value = remove_quotes(value)

                            # We are assuming `value` is in the form of "namespace:name:version"
                            split_dependency_string = value.split(':')
                            length = len(split_dependency_string)
                            if length == 3:
                                namespace, name, version = split_dependency_string
                                dependency['namespace'] = namespace
                                dependency['name'] = name
                                try:
                                    dependency['version'] = parse_version_str(version)
                                except Exception as e:
                                    logger.error(
                                        'Exception occurs in function parse_version_str '
                                        'when parsing build.gradle on {}: {}'.format(filepath, str(e)))
                                    dependency['version'] = ''
                            elif length == 2:
                                namespace, name = split_dependency_string
                                dependency['namespace'] = namespace
                                dependency['name'] = name
                                dependency['version'] = ''

                    if dependency and dependency['namespace']:
                        if dependency['namespace'] == 'pypi':
                            dependency['namespace'] = ''
                            dependency['type'] = 'pypi'
                            dependency['language'] = 'Python'
                        else:
                            dependency['name'] = dependency['namespace'] + '/' + dependency['name']
                            dependency['type'] = 'maven'
                            dependency['language'] = 'Java'
                        dependencies.append(dependency)

                if tree_node.label == 'DEPENDENCY-4':
                    dependency = {}
                    last_key = None
                    for child_node in tree_node.leaves():
                        if child_node.label == 'NAME-LABEL':
                            value = child_node.value
                            if value == 'group:':
                                last_key = 'namespace'
                            if value == 'name:':
                                last_key = 'name'
                            if value == 'version:':
                                last_key = 'version'
                        if is_literal_string(child_node.label):
                            if last_key == 'version':
                                try:
                                    dependency[last_key] = parse_version_str(remove_quotes(child_node.value))
                                except Exception as e:
                                    logger.error(
                                        'Exception occurs in function parse_version_str '
                                        'when parsing build.gradle on {}: {}'.format(filepath, str(e)))
                                    dependency[last_key] = ''
                            else:
                                dependency[last_key] = remove_quotes(child_node.value)

                    if dependency and dependency['namespace']:
                        dependency['name'] = dependency['namespace'] + '/' + dependency['name']
                        dependency['type'] = 'maven'
                        dependency['language'] = 'Java'
                        dependencies.append(dependency)

                # if tree_node.label == 'DEPENDENCY-5':
                #     dependency = {}
                #     for child_node in tree_node.leaves():
                #         if child_node.label == 'NAME-ATTRIBUTE':
                #             dependency['name'] = child_node.value
                #
                #     if dependency:
                #         dependency['type'] = 'maven'
                #         dependency['namespace'] = ''
                #         dependency['version'] = ''
                #         dependency['language'] = 'Java'
                #         dependencies.append(dependency)

    file.close()
    return dependencies


def get_dependency_tree(filepath, logger):

    result = list()

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        logger.error('Exception occurs when loading gradle_tree.txt file {}: {}'.format(filepath, str(e)))
        return result

    content = list()
    paragraph = list()
    for line in lines:
        if line != '\n':
            paragraph.append(line.rstrip('\n'))
        else:
            content.append(paragraph)
            paragraph = list()
    content.append(paragraph)

    for para in content:
        if len(para) > 1:
            temp = dict()
            temp['config'] = para[0]
            temp['tree'] = para[1:]
            result.append(temp)

    file.close()
    return result


def parse_gradle_tree_file(filepath, logger):

    dependencies = list()

    result = get_dependency_tree(filepath=filepath, logger=logger)
    if result:
        for item in result:
            # Java plugin dependency configurations: compileClasspath, runtimeClasspath, etc.
            # https://docs.gradle.org/current/userguide/java_plugin.html#sec:java_plugin_and_dependency_management
            if item['config'].startswith('compileClasspath') \
                    or item['config'].startswith('runtimeClasspath') \
                    or item['config'].startswith('testCompileClasspath') \
                    or item['config'].startswith('testRuntimeClasspath'):
                deps = item['tree']
                for dep in deps:
                    if '+---' in dep or '\\---' in dep:
                        if '+---' in dep and not dep.endswith('(*)'):
                            dep_info_str = dep.split('+---')[-1].strip('(c)').strip('(n)').strip()
                            dep_info = dep_info_str.split(':')
                            if len(dep_info) >= 3:
                                temp = dict()
                                temp['type'] = 'maven'
                                temp['namespace'] = dep_info[0]
                                temp['name'] = dep_info[0] + '/' + dep_info[1]
                                temp['version'] = dep_info[-1].split('->')[-1].strip()
                                temp['language'] = 'Java'
                                dependencies.append(temp)
                        elif '\\---' in dep and not dep.endswith('(*)'):
                            dep_info_str = dep.split('\\---')[-1].strip('(c)').strip('(n)').strip()
                            dep_info = dep_info_str.split(':')
                            if len(dep_info) >= 3:
                                temp = dict()
                                temp['type'] = 'maven'
                                temp['namespace'] = dep_info[0]
                                temp['name'] = dep_info[0] + '/' + dep_info[1]
                                temp['version'] = dep_info[-1].split('->')[-1].strip()
                                temp['language'] = 'Java'
                                dependencies.append(temp)

    dependencies = remove_duplicate_dict_items(data_list=dependencies)
    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    build_gradle_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/gradle/gradle-java/gradle-download-task/build.gradle'
    gradle_tree_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/gradle/gradle-java/gradle-download-task/gradle_tree.txt'
    log = Logger(path='../../log_dir/gradle-java_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = parse_build_gradle_file(filepath=build_gradle_location, logger=log)
    # dep_result = parse_gradle_tree_file(filepath=gradle_tree_location, logger=log)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
