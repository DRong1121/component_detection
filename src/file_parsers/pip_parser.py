import os
import ast

import pip_requirements_parser
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


def is_setup(filepath):
    if filepath.endswith('setup.py'):
        return True
    else:
        return False


def get_setup_args(filepath, logger):
    """
    Return a mapping of arguments passed to a setup.py setup() function.
    """
    setup_args = {}

    try:
        with open(file=filepath, mode='r') as inp:
            setup_text = inp.read()

        # parse setup.py and traverse the AST
        tree = ast.parse(setup_text)

    except Exception as e:
        logger.error('Exception occurs when loading setup.py file {}: {}'.format(filepath, str(e)))
        return setup_args

    for statement in tree.body:
        # We only care about function calls or assignments to functions named `setup` or `main`
        if not (
                isinstance(statement, (ast.Expr, ast.Call, ast.Assign))
                and isinstance(statement.value, ast.Call)
                and isinstance(statement.value.func, ast.Name)
                and statement.value.func.id in ('setup', 'main')
        ):
            continue

        # Process the arguments of the setup function
        for kw in getattr(statement.value, 'keywords', []):
            arg_name = kw.arg

            # 参数值为String
            if isinstance(kw.value, ast.Str):
                setup_args[arg_name] = kw.value.s

            # 参数值为List, Tuple, Set
            elif isinstance(kw.value, (ast.List, ast.Tuple, ast.Set,)):
                v = [
                    elt.s for elt in kw.value.elts
                    if
                    not isinstance(elt, ast.Call) and not isinstance(elt, ast.BinOp) and not isinstance(elt, ast.Name)
                ]
                setup_args[arg_name] = v

            # 参数值为Dict
            elif isinstance(kw.value, ast.Dict):
                rhs = {}
                for key, value in zip(kw.value.keys, kw.value.values):
                    # parse ast.Dict key
                    if isinstance(key, ast.Str):
                        if key.s:
                            k = key.s
                        else:
                            continue
                    else:
                        continue
                    # parse ast.Dict value
                    if isinstance(value, ast.Str):
                        v = value.s
                    elif isinstance(value, (ast.List, ast.Tuple, ast.Set,)):
                        v = [
                            elt.s for elt in value.elts
                            if not isinstance(elt, ast.Call) and not isinstance(elt, ast.BinOp)
                               and not isinstance(elt, ast.Name)
                        ]
                    else:
                        v = ''
                    rhs[k] = v
                setup_args[arg_name] = rhs

            # 参数值为变量
            elif isinstance(kw.value, ast.Name):
                kw_id = kw.value.id
                # 遍历语法树，获取变量对应的值
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        target = node.targets[0]
                        if isinstance(target, ast.Name) and target.id == kw_id:
                            # 变量类型为String
                            if isinstance(node.value, ast.Str):
                                v = node.value.s
                            # 变量类型为List, Tuple, Set
                            elif isinstance(node.value, (ast.List, ast.Tuple, ast.Set,)):
                                v = [
                                    elt.s for elt in node.value.elts
                                    if not isinstance(elt, ast.Call) and not isinstance(elt, ast.BinOp)
                                       and not isinstance(elt, ast.Name)
                                ]
                            # 变量类型为Dict
                            elif isinstance(node.value, ast.Dict):
                                v = {}
                                for key, value in zip(node.value.keys, node.value.values):
                                    # parse ast.Dict key
                                    if isinstance(key, ast.Str):
                                        if key.s:
                                            new_key = key.s
                                        else:
                                            continue
                                    else:
                                        continue
                                    # parse ast.Dict value
                                    if isinstance(value, ast.Str):
                                        new_value = value.s
                                    elif isinstance(value, (ast.List, ast.Tuple, ast.Set,)):
                                        new_value = [
                                            elt.s for elt in value.elts
                                            if not isinstance(elt, ast.Call)
                                               and not isinstance(elt, ast.BinOp) and not isinstance(elt, ast.Name)
                                        ]
                                    else:
                                        new_value = ''
                                    v[new_key] = new_value
                            # 变量为其他类型
                            else:
                                v = ''
                            setup_args[arg_name] = v
                            break

    inp.close()
    return setup_args


def is_simple_requires(requires):
    """
    Return True if ``requires`` is a sequence of strings.
    """
    return (
        requires
        and isinstance(requires, list)
        and all(isinstance(i, str) for i in requires)
    )


def get_requires_dependencies(requires):
    """
    Return a list of DependentPackage found in a ``requires`` list of
    requirement strings or an empty list.
    """
    dependencies = list()

    if not is_simple_requires(requires):
        return dependencies

    for req in (requires or []):
        req = Requirement(req)
        temp = dict()
        temp['type'] = 'pypi'
        temp['namespace'] = ''
        name = canonicalize_name(req.name)
        temp['name'] = name
        version_str = ''

        # note: packaging.requirements.Requirement.specifier is a packaging.specifiers.SpecifierSet object
        # and a SpecifierSet._specs is
        # a set of either 'packaging.specifiers.Specifier' or 'packaging.specifiers.LegacySpecifier'
        # and each of these have a .operator and .version property
        if req.specifier:
            specifiers_set = req.specifier  # a list of packaging.specifiers.Specifier
            specifiers = specifiers_set._specs
            # SpecifierSet stringifies to comma-separated sorted Specifiers
            if len(specifiers) == 1:
                specifier = list(specifiers)[0]
                if specifier.operator in ('==', '==='):
                    version_str = specifier.version
                elif specifier.operator == '~=':
                    nums = specifier.version.split('.')

                    lower = '.'.join(nums)
                    nums[-1] = '*'
                    upper = '.'.join(nums)
                    version_str = '>=' + lower + ', ' + '==' + upper
                else:
                    version_str = str(specifier)
            else:
                version_list = list()
                for specifier in specifiers:
                    version_list.append(str(specifier))
                version_str = ', '.join(version_list)
        temp['version'] = version_str
        temp['language'] = 'Python'

        if temp['name']:
            dependencies.append(temp)

    return dependencies


def parse_setup(setup_args):
    """
    Return a list of DependentPackage found in a ``setup_args`` mapping of
    setup.py arguments or an empty list.
    """
    dependencies = list()

    install_requires = setup_args.get('install_requires', [])
    dependencies.extend(get_requires_dependencies(install_requires))

    extras_require = setup_args.get('extras_require', {})
    for _, requires in extras_require.items():
        dependencies.extend(get_requires_dependencies(requires))

    tests_require = setup_args.get('tests_require', [])
    dependencies.extend(get_requires_dependencies(tests_require))

    setup_requires = setup_args.get('setup_requires', [])
    dependencies.extend(get_requires_dependencies(setup_requires))

    return dependencies


def parse_requirements(filepath, logger):
    """
        Return a list of DependentPackage found in a requirements file at
        ``filepath`` or an empty list.
    """
    dependencies = list()

    try:
        req_file = pip_requirements_parser.RequirementsFile.from_file(filename=filepath, include_nested=False)
    except Exception as e:
        logger.error('Exception occurs when loading requirements.txt file {}: {}'.format(filepath, str(e)))
        return dependencies

    if not req_file or not req_file.requirements:
        return dependencies

    for req in req_file.requirements:
        if req.name:
            temp = dict()
            temp['type'] = 'pypi'
            temp['namespace'] = ''
            name = canonicalize_name(req.name)
            temp['name'] = name
            version_str = ''
            if req.specifier:
                specifiers_set = req.specifier
                specifiers = specifiers_set._specs
                # SpecifierSet stringifies to comma-separated sorted Specifiers
                if len(specifiers) == 1:
                    specifier = list(specifiers)[0]
                    if specifier.operator in ('==', '==='):
                        version_str = specifier.version
                    elif specifier.operator == '~=':
                        nums = specifier.version.split('.')

                        lower = '.'.join(nums)
                        nums[-1] = '*'
                        upper = '.'.join(nums)
                        version_str = '>=' + lower + ', ' + '==' + upper
                    else:
                        version_str = str(specifier)
                else:
                    version_list = list()
                    for specifier in specifiers:
                        version_list.append(str(specifier))
                    version_str = ', '.join(version_list)
            temp['version'] = version_str
            temp['language'] = 'Python'
            dependencies.append(temp)

    return dependencies


def parse_pip_files(filepath, logger):

    if is_setup(filepath=filepath):
        setup_args = get_setup_args(filepath=filepath, logger=logger)
        dependencies = parse_setup(setup_args=setup_args)
    else:
        dependencies = parse_requirements(filepath=filepath, logger=logger)

    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    setup_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/python/gunicorn-20.0.4/setup.py'
    require_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/python/gunicorn-20.0.4/requirements_test.txt'
    log = Logger(path='../../log_dir/pip_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = list()
    # pip_deps = parse_pip_files(filepath=setup_location, logger=log)
    pip_deps = parse_pip_files(filepath=require_location, logger=log)
    dep_result.extend(pip_deps)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
