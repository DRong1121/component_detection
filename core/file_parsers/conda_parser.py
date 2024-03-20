import yaml
import fnmatch

from packaging.requirements import InvalidRequirement
from packaging.requirements import Requirement as PackagingRequirement
from packaging.utils import canonicalize_name

from dparse2.dependencies import Dependency, DependencyFile

default_library_names = (
    'ca-certificates',
    'certifi',
    'cffi',
    'cryptography',
    'libcxx',
    'libffi',
    'ncurses',
    'openssl',
    'pip',
    'python',
    'readline',
    'setuptools',
    'sqlite',
    'tk',
    'wheel',
    'xz',
    'zlib',
    '*conda*',
    'jupyter'
)


# this is a backport from setuptools 26.1
def setuptools_parse_requirements_backport(strs):
    """
    Yield ``Requirement`` objects for each specification in `strs`
    `strs` must be a string, or a (possibly-nested) iterable thereof.
    """
    # create a steppable iterator, so we can handle \-continuations
    def yield_lines(strs):
        """Yield non-empty/non-comment lines of a string or sequence"""
        if isinstance(strs, str):
            for s in strs.splitlines():
                s = s.strip()
                # skip blank lines/comments
                if s and not s.startswith("#"):
                    yield s
        else:
            for ss in strs:
                for s in yield_lines(ss):
                    yield s

    lines = iter(yield_lines(strs))

    for line in lines:
        # Drop comments -- a hash without a space may be in a URL.
        if " #" in line:
            line = line[: line.find(" #")]
        # If there is a line continuation, drop it, and append the next line.
        if line.endswith("\\"):
            line = line[:-2].strip()
            line += next(lines)
        yield PackagingRequirement(line)


def parse_requirement_line(line):
    try:
        # setuptools requires a space before the comment. If this isn't the case, add it.
        if "\t#" in line:
            (parsed,) = setuptools_parse_requirements_backport(line.replace("\t#", "\t #"))
        else:
            (parsed,) = setuptools_parse_requirements_backport(line)

    except InvalidRequirement:
        return

    dep = Dependency(
        name=parsed.name,
        specs=parsed.specifier,
        line=line,
        extras=parsed.extras,
        dependency_type="requirements.txt",
    )
    return dep


class Parser(object):

    def __init__(self, obj):
        self.obj = obj
        self._lines = None

    @property
    def lines(self):
        if self._lines is None:
            self._lines = self.obj.content.splitlines()
        return self._lines


class CondaYMLParser(Parser):

    def parse(self):
        try:
            data = yaml.safe_load(self.obj.content) or {}
            if isinstance(data, dict):
                dependencies = data.get("dependencies") or []
                for dep in dependencies:
                    if isinstance(dep, str):
                        # filter hash string
                        dep = dep.rsplit('=', 1)[0]
                        # replace '=' with '=='
                        if ('=' in dep) and ('<=' not in dep) and ('>=' not in dep) and ('!=' not in dep):
                            count = dep.count('=')
                            dep = dep.replace('='*count, '==')
                        req = parse_requirement_line(dep)
                        if req:
                            req.dependency_type = self.obj.file_name
                            self.obj.dependencies.append(req)
                    elif isinstance(dep, dict):
                        lines = dep.get("pip") or []
                        for line in lines:
                            req = parse_requirement_line(line)
                            if req:
                                req.dependency_type = self.obj.file_name
                                self.obj.dependencies.append(req)
        except yaml.YAMLError:
            pass


def parse_func(content, file_name=None, path=None, parser=None):
    dep_file = DependencyFile(
        content=content,
        path=path,
        file_name=file_name,
        parser=parser,
    )
    return dep_file.parse()


def parse_environment_file(filepath, logger):

    dependencies = list()

    try:
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            content = file.read()
        dep_file = parse_func(content=content, file_name='conda.yml', parser=CondaYMLParser)
    except Exception as e:
        logger.error('Exception occurs when loading environment.yaml file {}: {}'.format(filepath, str(e)))
        return dependencies

    if not dep_file:
        file.close()
        return dependencies

    if dep_file.dependencies:
        for dependency in dep_file.dependencies:
            temp = dict()
            temp['type'] = 'pypi'
            temp['namespace'] = ''
            temp['name'] = canonicalize_name(dependency.name)

            is_default_lib = any(fnmatch.fnmatchcase(temp['name'], lib) for lib in default_library_names)
            if not is_default_lib:
                version_str = ''
                if dependency.specs:
                    specifiers_set = dependency.specs  # a list of packaging.specifiers.Specifier
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

    file.close()
    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    environment_location = '/Users/rongdang/Desktop/scripts/ci/org.centos/build-environment.yml'
    log = Logger(path='../../log_dir/conda_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = list()
    environment_deps = parse_environment_file(filepath=environment_location, logger=log)
    dep_result.extend(environment_deps)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
