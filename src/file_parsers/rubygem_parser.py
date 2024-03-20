from gemfileparser import GemfileParser


def parse_version_list(requirement):

    for i in range(0, len(requirement)):
        requirement[i] = requirement[i].replace(' ', '')
        req = requirement[i]
        if req.startswith('='):
            requirement[i] = req.split('=')[-1]
        elif req.startswith('~>'):
            flag = ''
            if '-' in req:
                flag = '-' + req.split('-')[-1]
                req = req.split('-')[0]

            req = req.split('~>')[-1]
            if not req.replace('.', '').isdigit():
                flag = '.' + req.split('.')[-1]
                nums = req.split('.')[:-1]
            else:
                nums = req.split('.')

            if len(nums) == 1:
                nums.append('0')

            lower = '.'.join(nums)
            nums[-2] = str(int(nums[-2]) + 1)
            nums[-1] = '0'
            upper = '.'.join(nums)

            if not flag:
                requirement[i] = '>=' + lower + ', ' + '<' + upper
            else:
                requirement[i] = '>=' + lower + flag + ', ' + '<' + upper

    return ' && '.join(requirement)


def parse_rubygem_files(filepath, logger):
    """
    Parse Ruby .gemspec and Gemfile.
    Return a mapping of dependency data parsed from a gemspec/Gemfile file at ``location``.
    """
    dependencies = list()

    try:
        parser = GemfileParser(filepath=filepath)
    except Exception as e:
        logger.error('Exception occurs when loading gemspec or Gemfile {}: {}'.format(filepath, str(e)))
        return dependencies

    parsed_result = parser.parse()

    for key in parsed_result:
        deps = parsed_result.get(key, []) or []
        for dep in deps:
            # print(dep.name)
            # print(dep.requirement)
            temp = dict()
            temp['type'] = 'gem'
            temp['namespace'] = ''
            temp['name'] = dep.name
            try:
                temp['version'] = parse_version_list(dep.requirement) if dep.requirement else ''
            except Exception as e:
                logger.error('Exception occurs in function parse_version_list when parsing gemspec or Gemfile on {}: {}'
                             .format(filepath, str(e)))
                continue
            temp['language'] = 'Ruby'

            if temp['name'] and temp['name'] != 'platforms':
                dependencies.append(temp)

    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    gemspec_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/ruby/gem_updater/gem_updater.gemspec'
    gemfile_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/ruby/annotate_gem/test/fixtures/Gemfile'
    log = Logger(path='../../log_dir/ruby_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = list()
    # gemspec_deps = parse_rubygem_files(filepath=gemspec_location, logger=log)
    # dep_result.extend(gemspec_deps)
    gemfile_deps = parse_rubygem_files(filepath=gemfile_location, logger=log)
    dep_result.extend(gemfile_deps)
    if dep_result:
        print(len(dep_result))
        for item in dep_result:
            print(item)
