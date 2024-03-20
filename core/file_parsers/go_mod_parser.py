import io
import re


def is_gosum(filepath):
    if filepath.endswith('go.sum'):
        return True
    else:
        return False


def preprocess(line):
    """
    Return line string after removing commented portion and excess spaces.
    """
    if "//" in line:
        line = line[:line.index('//')]
    line = line.strip()
    return line


"""
This part handles go.mod files from Go.
See https://golang.org/ref/mod#go.mod-files for details

For example:

module example.com/my/thing

go 1.12

require example.com/other/thing v1.0.2
require example.com/new/thing v2.3.4
exclude example.com/old/thing v1.2.3
require (
    example.com/new/thing v2.3.4
    example.com/old/thing v1.2.3
)
require (
    example.com/new/thing v2.3.4
    example.com/old/thing v1.2.3
)

"""

"""
module is in the form
require github.com/davecgh/go-spew v1.1.1
or
exclude github.com/davecgh/go-spew v1.1.1
or
module github.com/alecthomas/participle

For example:
>>> p = parse_module('module github.com/alecthomas/participle')
>>> assert p.group('type') == ('module')
>>> assert p.group('ns_name') == ('github.com/alecthomas/participle')

>>> p = parse_module('require github.com/davecgh/go-spew v1.1.1')
>>> assert p.group('type') == ('require')
>>> assert p.group('ns_name') == ('github.com/davecgh/go-spew')
>>> assert p.group('version') == ('v1.1.1')

require or exclude can be in the form
github.com/davecgh/go-spew v1.1.1

For example:
>>> p = parse_dep_link('github.com/davecgh/go-spew v1.1.1')
>>> assert p.group('namespace') == ('github.com/davecgh')
>>> assert p.group('name') == ('go-spew')
>>> assert p.group('version') == ('v1.1.1')
"""

# Regex expressions to parse different types of go.mod file dependency
parse_module = re.compile(
    r'(?P<type>[^\s]+)'
    r'(\s)+'
    r'(?P<ns_name>[^\s]+)'
    r'\s?'
    r'(?P<version>(.*))'
).match

parse_dep_link = re.compile(
    r'.*?'
    r'(?P<ns_name>[^\s]+)'
    r'\s+'
    r'(?P<version>(.*))'
).match


def parse_gomod(filepath, logger):
    """
    Return a dictionary containing all the important go.mod file data.
    """
    dependencies = list()

    try:
        with io.open(filepath, encoding='utf-8', closefd=True) as data:
            lines = data.readlines()
    except Exception as e:
        logger.error('Exception occurs when loading go.mod file {}: {}'.format(filepath, str(e)))
        return dependencies

    for i, line in enumerate(lines):
        line = preprocess(line)

        if 'require' in line and '(' in line:
            for req in lines[i + 1:]:
                req = preprocess(req)
                if ')' in req:
                    break
                parsed_dep_link = parse_dep_link(req)
                if parsed_dep_link:
                    ns_name = parsed_dep_link.group('ns_name')
                    namespace, _, name = ns_name.rpartition('/')
                    version = parsed_dep_link.group('version').lstrip('v')

                    temp = dict()
                    temp['type'] = 'golang'
                    temp['namespace'] = namespace
                    temp['name'] = name
                    temp['version'] = version
                    temp['language'] = 'Go'
                    dependencies.append(temp)
            # get next line
            continue

        if 'exclude' in line and '(' in line:
            # get next line
            continue

        parsed_module_name = parse_module(line)
        if parsed_module_name:
            ns_name = parsed_module_name.group('ns_name')
            namespace, _, name = ns_name.rpartition('/')
            version = parsed_module_name.group('version').lstrip('v')
            if 'require' in line:
                temp = dict()
                temp['type'] = 'golang'
                temp['namespace'] = namespace
                temp['name'] = name
                temp['version'] = version
                temp['language'] = 'Go'
                dependencies.append(temp)
            continue

    return dependencies


"""
This part handles go.sum files from Go.
See https://blog.golang.org/using-go-modules for details

A go.sum file contains pinned Go modules checksums of two styles:

For example:
github.com/BurntSushi/toml v0.3.1 h1:WXkYYl6Yr3qBf1K79EBnL4mak0OimBfB0XUf9Vl28OQ=
github.com/BurntSushi/toml v0.3.1/go.mod h1:xHWCNGjB5oqiDr8zfno3MHue2Ht5sIBksp03qcyfWMU=

... where the line with /go.mod is for a check of that go.mod file 
and the other line contains a dirhash for that path as documented as
https://pkg.go.dev/golang.org/x/mod/sumdb/dirhash

Here are some example of usage of this module::

>>> p = get_dependency('github.com/BurntSushi/toml v0.3.1 h1:WXkYYl6Yr3qBf1K79EBnL4mak0OimBfB0XUf9Vl28OQ=')
>>> assert p.group('ns_name') == ('github.com/BurntSushi/toml')
>>> assert p.group('version') == ('v0.3.1')
>>> assert p.group('checksum') == ('WXkYYl6Yr3qBf1K79EBnL4mak0OimBfB0XUf9Vl28OQ=')
"""

# Regex expressions to parse go.sum file dependency
# dep example: github.com/BurntSushi/toml v0.3.1 h1:WXkYY....
get_dependency = re.compile(
    r'(?P<ns_name>[^\s]+)'
    r'\s+'
    r'(?P<version>[^\s]+)'
    r'\s+'
    r'h1:(?P<checksum>[^\s]*)'
).match


def parse_gosum(filepath, logger):
    """
    Return a list of GoSum from parsing the go.sum file at `location`.
    """
    dependencies = list()

    try:
        with io.open(filepath, encoding='utf-8', closefd=True) as data:
            lines = data.readlines()
    except Exception as e:
        logger.error('Exception occurs when loading go.sum file {}: {}'.format(filepath, str(e)))
        return dependencies

    temp = dict()
    for line in lines:
        line = line.replace('/go.mod', '')
        parsed_dep = get_dependency(line)
        ns_name = parsed_dep.group('ns_name')
        version = parsed_dep.group('version').lstrip('v')
        temp.update({ns_name: version})

    for ns, ver in temp.items():
        namespace, _, name = ns.rpartition('/')
        dep = dict()
        dep['type'] = 'golang'
        dep['namespace'] = namespace
        dep['name'] = name
        dep['version'] = ver
        dep['language'] = 'Go'
        dependencies.append(dep)

    return dependencies


def parse_gomod_files(filepath, logger):

    if is_gosum(filepath=filepath):
        dependencies = parse_gosum(filepath=filepath, logger=logger)
    else:
        dependencies = parse_gomod(filepath=filepath, logger=logger)

    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    gomod_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/golang/kubernetes-1.19.4/go.mod'
    gosum_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/golang/kubernetes-1.19.4/go.sum'
    log = Logger(path='../../log_dir/gomod_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    gomod_result = parse_gomod_files(filepath=gomod_location, logger=log)
    if gomod_result:
        print(len(gomod_result))
        for item in gomod_result:
            print(item)

    gosum_result = parse_gomod_files(filepath=gosum_location, logger=log)
    if gosum_result:
        print(len(gosum_result))
        for item in gosum_result:
            print(item)
