from core.util import read_temp_json_file


def url_decoder(package_info):
    package_info = package_info.replace('%00', '')
    package_info = package_info.replace('%0A', '')
    package_info = package_info.replace('%EF', '')
    package_info = package_info.replace('%BF', '')
    package_info = package_info.replace('%BD', '')

    package_info = package_info.replace('%20', ' ')
    package_info = package_info.replace('%21', '!')
    package_info = package_info.replace('%22', '"')
    package_info = package_info.replace('%23', '#')
    package_info = package_info.replace('%24', '$')
    package_info = package_info.replace('%28', '(')
    package_info = package_info.replace('%29', ')')
    package_info = package_info.replace('%2B', '+')
    package_info = package_info.replace('%2C', ',')
    package_info = package_info.replace('%2F', '/')

    package_info = package_info.replace('%3A', ':')
    package_info = package_info.replace('%3B', ';')
    package_info = package_info.replace('%3C', '<')
    package_info = package_info.replace('%3D', '=')
    package_info = package_info.replace('%3E', '>')
    package_info = package_info.replace('%3F', '?')
    package_info = package_info.replace('%40', '@')
    package_info = package_info.replace('%5E', '')
    package_info = package_info.replace('%7B', '{')
    package_info = package_info.replace('%7D', '}')
    package_info = package_info.replace('%7E', '~')

    return package_info


def get_language_by_type(type):
    language = ''
    if type == 'nuget':
        language = 'C#'
    elif type == 'pub':
        language = 'Dart'
    elif type == 'golang':
        language = 'Go'
    elif type == 'maven':
        language = 'Java'
    elif type == 'npm':
        language = 'Node JS'
    elif type == 'cocoapods':
        language = 'Objective C'
    elif type == 'cpan':
        language = 'Perl'
    elif type == 'pypi':
        language = 'Python'
    elif type == 'gem':
        language = 'Ruby'
    elif type == 'swift':
        language = 'Swift'

    return language


def parse_pypi_name_and_version(package_url):
    package_str = package_url.split('/')[-1].split('@')[0]
    package_str = url_decoder(package_info=package_str).replace(' ', '')
    if ';' in package_str:
        package_str = package_str.split(';')[0]
    if '#' in package_str:
        package_str = package_str.split('#')[0]

    if package_str:
        if '==' in package_str:
            name = package_str.split('==')[0].strip()
            version = package_str.split('==')[-1].strip()
        elif '~=' in package_str:
            name = package_str.split('~=')[0].strip()
            nums = package_str.split('~=')[-1].strip().split('.')

            lower = '.'.join(nums)
            nums[-1] = '*'
            upper = '.'.join(nums)
            version = '>=' + lower + ',' + '==' + upper
        elif '>' in package_str:
            if '>=' in package_str:
                name = package_str.split('>=')[0].strip()
                version = '>=' + package_str.split('>=')[-1].strip()
            else:
                name = package_str.split('>')[0].strip()
                version = '>' + package_str.split('>')[-1].strip()
        elif '>' not in package_str and '<' not in package_str and '!=' in package_str:
            name = package_str.split('!=')[0].strip()
            version = '!=' + package_str.split('!=')[-1].strip()
        else:
            if not package_str.startswith('-r') and not package_str.endswith('.whl'):
                name = package_str.strip()
                if '@' in package_url:
                    version = package_url.split('@')[1]
                    version = url_decoder(package_info=version)
                    if ';' in version:
                        version = version.split(';')[0].strip()
                    if '#' in version:
                        version = version.split('#')[0].strip()
                else:
                    version = ''
            # package_str.startswith('-r') or package_str.endswith('.whl')
            else:
                name = ''
                version = ''
    # package_str is None
    else:
        name = ''
        version = ''

    return name, version


def parse_name_and_version(package_url):
    name = package_url.split('/')[-1].split('@')[0]
    name = url_decoder(package_info=name)

    if '@' in package_url:
        version = package_url.split('@')[1]
        version = url_decoder(package_info=version)
    else:
        version = ''

    return name, version


def parse_temp_file(temp_file_path, logger):

    dep_result = dict()

    # load json file
    json_result = read_temp_json_file(filepath=temp_file_path, logger=logger)

    if json_result:
        # parse json file
        if json_result['dependencies']:
            for dependency in json_result['dependencies']:
                # add package info
                try:
                    for package in dependency['packages']:
                        try:
                            package_id = package['id']
                            if (package_id.startswith('pkg:')) and (package_id not in dep_result.keys()):
                                # reference to: https://github.com/package-url/purl-spec
                                dep_item = dict()
                                package_id = package_id.split('#')[0].split('?')[0]

                                type = package_id.split('pkg:')[1].split('/')[0]
                                if len(package_id.split('/')) == 3:
                                    namespace = package_id.split('/')[1]
                                    namespace = url_decoder(package_info=namespace)
                                elif len(package_id.split('/')) > 3:
                                    namespace = '/'.join(package_id.split('/')[1:len(package_id.split('/'))-1])
                                    namespace = url_decoder(package_info=namespace)
                                else:
                                    namespace = ''

                                # name, version = parse_name_and_version(package_url=package_id)
                                if package_id.startswith('pkg:pypi/'):
                                    name, version = parse_pypi_name_and_version(package_url=package_id)
                                else:
                                    name, version = parse_name_and_version(package_url=package_id)

                                if name:
                                    dep_item['type'] = type
                                    dep_item['namespace'] = namespace
                                    dep_item['name'] = name
                                    dep_item['version'] = version
                                    dep_item['language'] = get_language_by_type(type)
                                    dep_result[package_id] = dep_item
                        except Exception as e:
                            logger.error('Subprocess exception: exception occurs when parsing dependency-check result '
                                         'temp json file: {}'.format(str(e)))
                            continue
                except KeyError:
                    pass

    else:
        logger.error('Subprocess exception: exception occurs when loading dependency-check result temp json file!')

    return dep_result


if __name__ == "__main__":

    # result_dir = '/Users/rongdang/Desktop/sca-2.0/check_result_dir'
    # _list = os.walk(result_dir)
    # for root, _, files in _list:
    #     for file in files:
    #         file_path = os.path.join(root, file)
    #         print('Current file: ', file_path)
    #         json_result = file_iterator(filepath=file_path)
    #         if json_result:
    #             # print('File result: ' + str(len(json_result['file_result'])))
    #             print('Dep result: ' + str(len(json_result['dep_result'].keys())))

    package_url = 'pkg:golang/cloud.google.com/go@v0.16.0#comput/metadata'
    package_url = package_url.split('#')[0].split('?')[0]
    print(package_url)

    # if package_url.startswith('pkg:pypi/'):
    #     package_name, package_version = parse_pypi_name_and_version(package_url=package_url)
    #     print(package_name)
    #     print(package_version)
