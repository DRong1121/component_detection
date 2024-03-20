import re
from core.file_parsers.gemfile_lock_utils import unicode_text_lines
from core.util import remove_duplicate_dict_items


OPTIONS = re.compile(r'^  (?P<key>[a-z]+): (?P<value>.*)$').match
SUPPORTED_OPTS = ['remote', 'ref', 'revision', 'branch', 'submodules', 'tag']


def get_option(s):
    """
    Parse Gemfile.lock options such as remote, ref, revision, etc.
    """
    key = None
    value = None

    opts = OPTIONS(s)
    if opts:
        key = opts.group('key') or None
        value = opts.group('value') or None
        # normalize truth
        if value == 'true':
            value = True
        if value == 'false':
            value = False
        # only keep known options, discard others
        if key not in SUPPORTED_OPTS:
            key = None
            value = None

    return key, value


# Section headings: these are also used as switches to track a parsing state
PATH = 'PATH'
GIT = 'GIT'
SVN = 'SVN'
GEM = 'GEM'
PLATFORMS = 'PLATFORMS'
DEPENDENCIES = 'DEPENDENCIES'
SPECS = '  specs:'
# types of Gems, which is really where they are provisioned from RubyGems repo, local path or VCS
GEM_TYPES = (GEM, PATH, GIT, SVN,)


class Gem(object):
    """
    A Gem can be packaged as a .gem archive, or it can be a source gem
    either fetched from GIT or SVN or from a local path.
    """
    def __init__(self, name, version=None, platform=None):
        self.name = name
        self.version = version
        self.platform = platform

        self.remote = ''
        self.type = ''
        # relative path
        self.path = ''

        self.revision = ''
        self.ref = ''
        self.spec_version = ''

        self.pinned = bool()
        self.branch = ''
        self.submodules = ''
        self.tag = ''

        self.requirements = list()
        self.dependencies = dict()

    def refine(self):
        """
        Apply some refinements to the Gem based on its type:
         - fix version and revisions for Gems checked-out from VCS
        """
        if self.type == PATH:
            self.path = self.remote

        if self.type in (GIT, SVN,):
            self.spec_version = self.version
            if self.revision and not self.ref:
                self.version = self.revision
            elif self.revision and self.ref:
                self.version = self.revision
            elif not self.revision and self.ref:
                self.version = self.ref
            elif not self.revision and self.ref:
                self.version = self.ref


# parse name/version/platform
NAME_VERSION = (
    # negative lookahead: not a space
    '(?! )'
    # a Gem name: several chars are not allowed
    '(?P<name>[^ \\)\\(,!:]+)?'
    # a space then opening parens (
    '(?: \\('
    # the version proper which is anything but a dash
    '(?P<version>[^-]*)'
    # and optionally some non-captured dash followed by anything, once
    # pinned version can have this form:
    # version-platform
    # json (1.8.0-java) alpha (1.9.0-x86-mingw32) and may not contain a !
    '(?:-(?P<platform>[^!]*))?'
    # closing parens )
    '\\)'
    # NV is zero or one time
    ')?')

# parse direct dependencies
DEPS = re.compile(
    # two spaces at line start
    '^ {2}'
    # NV proper
    '%(NAME_VERSION)s'
    # optional bang pinned
    '(?P<pinned>!)?'
    '$' % locals()).match

# parse spec-level dependencies
SPEC_DEPS = re.compile(
    # four spaces at line start
    '^ {4}'
    '%(NAME_VERSION)s'
    '$' % locals()).match

# parse direct dependencies on spec
SPEC_SUB_DEPS = re.compile(
    # six spaces at line start
    '^ {6}'
    '%(NAME_VERSION)s'
    '$' % locals()).match

PLATS = re.compile('^  (?P<platform>.*)$').match


class GemfileLock:
    """
    Parse Gemfile.lock. Code originally derived from Bundler's /bundler/lib/bundler/lockfile_parser.rb parser
    The parser uses a simple state machine, switching states based on sections headings.
    The result is a tree of Gems objects stored in self.dependencies.
    """
    def __init__(self, lockfile):
        self.lockfile = lockfile

        # map of a line start string to the next parsing state function
        self.STATES = {
            DEPENDENCIES: self.parse_dependency,
            PLATFORMS: self.parse_platform,
            GIT: self.parse_options,
            PATH: self.parse_options,
            SVN: self.parse_options,
            GEM: self.parse_options,
            SPECS: self.parse_spec
        }

        # the final tree of dependencies, keyed by name
        self.dependency_tree = {}

        # a flat dict of all gems, keyed by name
        self.all_gems = {}

        self.platforms = []

        # init parsing state
        self.reset_state()

        # parse proper
        for line in unicode_text_lines(lockfile):
            line = line.rstrip()

            # reset state
            if not line:
                self.reset_state()
                continue

            # switch to new state
            if line in self.STATES:
                if line in GEM_TYPES:
                    self.current_type = line
                self.state = self.STATES[line]
                continue

            # process state
            if self.state:
                self.state(line)

        # finally refine the collected data
        self.refine()

    def reset_state(self):
        self.state = None
        self.current_options = {}
        self.current_gem = None
        self.current_type = None

    def refine(self):
        for gem in self.all_gems.values():
            gem.refine()

    def get_or_create(self, name, version=None, platform=None):
        """
        Return an existing gem if it exists or creates a new one.
        Update the all_gems registry.
        """
        if name in self.all_gems:
            gem = self.all_gems[name]
            gem.version = gem.version or version
            gem.platform = gem.platform or platform
        else:
            gem = Gem(name, version, platform)
            self.all_gems[name] = gem
        return gem

    def parse_options(self, line):
        key, value = get_option(line)
        if key:
            self.current_options[key] = value

    def parse_spec(self, line):
        spec_dep = SPEC_DEPS(line)
        if spec_dep:
            name = spec_dep.group('name')
            version = spec_dep.group('version')
            platform = spec_dep.group('platform') or 'ruby'

            # always set a new current gem
            self.current_gem = self.get_or_create(name, version, platform)
            self.current_gem.type = self.current_type

            if version:
                self.current_gem.version = version

            self.current_gem.platform = platform
            for k, v in self.current_options.items():
                setattr(self.current_gem, k, v)
            return

        spec_sub_dep = SPEC_SUB_DEPS(line)
        if spec_sub_dep:
            name = spec_sub_dep.group('name')
            if name == 'bundler':
                return

            requirements = spec_sub_dep.group('version') or []
            if requirements:
                requirements = [d.strip() for d in requirements.split(',')]

            if name in self.current_gem.dependencies:
                dep = self.current_gem.dependencies[name]
            else:
                dep = self.get_or_create(name)
                self.current_gem.dependencies[name] = dep

            if not dep.type:
                dep.type = GEM

            for v in requirements:
                if v not in dep.requirements:
                    dep.requirements.append(v)

    def parse_dependency(self, line):
        deps = DEPS(line)

        if not deps:
            return

        name = deps.group('name')

        # at this stage ALL gems should already exist except possibly
        # for bundler: not finding one is an error
        try:
            gem = self.all_gems[name]
        except KeyError as e:
            gem = Gem(name)
            self.all_gems[name] = gem

        if name not in self.dependency_tree:
            self.dependency_tree[name] = gem

        version = deps.group('version') or []
        if version:
            version = [v.strip() for v in version.split(',')]
            # the version of a direct dep is always a constraint
            # we append these at the top of the list as this is the main constraint
            for v in version:
                gem.requirements.insert(0, v)
            # assert gem.version == version

        gem.pinned = True if deps.group('pinned') else False

    def parse_platform(self, line):
        plat = PLATS(line)
        if not plat:
            return
        plat = plat.group('platform')
        self.platforms.append(plat.strip())


def parse_gemfile_lock_file(filepath, root_name, logger):

    dependencies = list()

    try:
        gemfile_lock = GemfileLock(lockfile=filepath)
    except Exception as e:
        logger.error('Exception occurs when loading Gemfile.lock file {}: {}'.format(filepath, str(e)))
        return dependencies

    for _, gem in gemfile_lock.all_gems.items():
        if gem.name != root_name:
            temp = dict()
            temp['type'] = 'gem'
            temp['namespace'] = ''
            temp['name'] = gem.name
            temp['version'] = gem.version if gem.version else ''
            temp['language'] = 'Ruby'
            dependencies.append(temp)

    for _, gem in gemfile_lock.all_gems.items():
        for _dep_name, dep in gem.dependencies.items():
            if dep.name != root_name:
                temp = dict()
                temp['type'] = 'gem'
                temp['namespace'] = ''
                temp['name'] = dep.name
                temp['version'] = dep.version if dep.version else ''
                temp['language'] = 'Ruby'
                dependencies.append(temp)

    dependencies = remove_duplicate_dict_items(data_list=dependencies)
    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    gemfile_lock_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/ruby/ciao/Gemfile.lock'
    log = Logger(path='../../log_dir/ruby_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = list()
    gemfile_lock_deps = parse_gemfile_lock_file(filepath=gemfile_lock_location, root_name='ciao', logger=log)
    dep_result.extend(gemfile_lock_deps)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
