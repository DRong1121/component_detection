import xml
import xml.etree.ElementTree as ET


def parse_version_str(version):
    if version.startswith('[') and version.endswith(']'):
        inner_str = version.lstrip('[').rstrip(']')
        nums = inner_str.split(',')
        if len(nums) == 1:
            version = nums[0].strip()
        else:
            version = '>=' + nums[0].strip() + ', ' + '<=' + nums[-1].strip()
        return version
    elif version.startswith('(') and version.endswith(')'):
        inner_str = version.lstrip('(').rstrip(')')
        if inner_str.startswith(','):
            version = '<' + inner_str.lstrip(',')
        elif inner_str.endswith(','):
            version = '>' + inner_str.rstrip(',')
        else:
            nums = inner_str.split(',')
            if len(nums) == 1:
                version = '无效版本号'
            else:
                version = '>' + nums[0].strip() + ', ' + '<' + nums[-1].strip()
        return version
    elif version.startswith('[') and version.endswith(')'):
        inner_str = version.lstrip('[').rstrip(')')
        nums = inner_str.split(',')
        if '' in nums:
            version = '>=' + nums[0].strip()
        else:
            version = '>=' + nums[0].strip() + ', ' + '<' + nums[-1].strip()
        return version
    elif version.startswith('(') and version.endswith(']'):
        inner_str = version.lstrip('(').rstrip(']')
        nums = inner_str.split(',')
        if '' in nums:
            version = '<=' + nums[-1].strip()
        else:
            version = '>' + nums[0].strip() + ', ' + '<=' + nums[-1].strip()
        return version
    elif version == '*-*':
        version = '包含不稳定版本的最高版本'
        return version
    elif version == '*':
        version = '最高稳定版本'
        return version
    elif version.endswith('*-*'):
        lower = version.replace('*-*', '0')
        nums = lower.split('.')
        nums[-2] = str(int(nums[-2]) + 1)
        upper = '.'.join(nums)
        version = '>=' + lower + ', ' + '<' + upper
        return version
    elif version.endswith('*'):
        lower = version.replace('*', '0')
        nums = lower.split('.')
        nums[-2] = str(int(nums[-2]) + 1)
        upper = '.'.join(nums)
        version = '>=' + lower + ', ' + '<' + upper
        return version
    else:
        version = '>=' + version
        return version


def get_xmlns(filepath, logger):

    xmlns = ''
    try:
        for evt, elem in ET.iterparse(filepath, ('start-ns', 'end-ns')):
            if evt == 'start-ns':
                try:
                    xmlns = elem[1]
                    break
                except IndexError:
                    pass

    except Exception as e:
        logger.error('Exception occurs when loading c# XML config file {}: {}'.format(filepath, str(e)))

    return xmlns


def get_xml_file_tree(filepath, logger):
    """
       desc: 获取当前xml文件的element tree
       params: filepath: str, 当前xml文件所在路径
       return: tree: ElementTree, xml文件加载后的返回值
    """
    try:
        tree = ET.ElementTree(file=filepath)
        return tree
    except Exception as e:
        logger.error('Exception occurs when loading c# XML config file {}: {}'.format(filepath, str(e)))
        return None


def parse_packages_config_file(filepath, logger):

    dependencies = list()

    tree = get_xml_file_tree(filepath=filepath, logger=logger)
    if tree:
        root = tree.getroot()
        if isinstance(root, xml.etree.ElementTree.Element):
            for child in root:
                try:
                    name = child.attrib['id']
                except KeyError:
                    continue

                try:
                    version = child.attrib['version']
                except KeyError:
                    version = ''

                temp = dict()
                temp['type'] = 'nuget'
                temp['namespace'] = ''
                temp['name'] = name
                temp['version'] = version
                temp['language'] = 'C#'
                dependencies.append(temp)

    return dependencies


def parse_nuspec_file(filepath, logger):

    dependencies = list()

    tree = get_xml_file_tree(filepath=filepath, logger=logger)
    if tree:
        # 获取package的name, version
        nuspec_namespace = get_xmlns(filepath=filepath, logger=logger)
        if nuspec_namespace:
            nuspec_namespace = '{' + nuspec_namespace + '}'
            package_id = tree.find(path='./' + nuspec_namespace + 'metadata' + '/' + nuspec_namespace + 'id')
            package_version = tree.find(path='./' + nuspec_namespace + 'metadata' + '/' + nuspec_namespace + 'version')
        else:
            package_id = tree.find(path='./metadata/id')
            package_version = tree.find(path='./metadata/version')

        package = dict()
        package['type'] = 'nuget'
        package['namespace'] = ''
        package['name'] = package_id.text if isinstance(package_id, xml.etree.ElementTree.Element) else ''
        package['version'] = package_version.text if isinstance(package_version, xml.etree.ElementTree.Element) else ''
        package['language'] = 'C#'
        if package['name']:
            dependencies.append(package)

        # 获取package的dependency列表
        if nuspec_namespace:
            node_list = tree.findall(path='.//' + nuspec_namespace + 'dependency')
        else:
            node_list = tree.findall(path='.//dependency')

        if node_list:
            for node in node_list:
                try:
                    name = node.attrib['id']
                except KeyError:
                    continue

                try:
                    version = node.attrib['version']
                except KeyError:
                    version = ''

                temp = dict()
                temp['type'] = 'nuget'
                temp['namespace'] = ''
                temp['name'] = name
                try:
                    temp['version'] = parse_version_str(version) if version else ''
                except Exception as e:
                    logger.error('Exception occurs in function parse_version_str when parsing nuspec file on {}: {}'
                                 .format(filepath, str(e)))
                    continue
                temp['language'] = 'C#'
                dependencies.append(temp)

    return dependencies


def parse_csproj_file(filepath, logger):

    dependencies = list()

    tree = get_xml_file_tree(filepath=filepath, logger=logger)
    if tree:
        # 获取PackageReference列表
        csproj_namespace = get_xmlns(filepath=filepath, logger=logger)
        if csproj_namespace:
            csproj_namespace = '{' + csproj_namespace + '}'
            node_list = tree.findall(path='.//' + csproj_namespace + 'PackageReference')
        else:
            node_list = tree.findall(path='.//PackageReference')

        if node_list:
            for node in node_list:
                try:
                    name = node.attrib['Include']
                except KeyError:
                    continue

                try:
                    version = node.attrib['Version']
                except KeyError:
                    version = ''

                if not version:
                    for child in node:
                        if child.tag == csproj_namespace + 'Version':
                            version = child.text
                            break
                        elif child.tag == 'Version':
                            version = child.text
                            break

                temp = dict()
                temp['type'] = 'nuget'
                temp['namespace'] = ''
                temp['name'] = name
                try:
                    temp['version'] = parse_version_str(version) if version else ''
                except Exception as e:
                    logger.error('Exception occurs in function parse_version_str when parsing csproj file on {}: {}'
                                 .format(filepath, str(e)))
                    continue
                temp['language'] = 'C#'
                dependencies.append(temp)

    return dependencies


def parse_nuget_files(filepath, logger):

    dependencies = list()

    if filepath.endswith('packages.config'):
        dependencies = parse_packages_config_file(filepath=filepath, logger=logger)
    elif filepath.endswith('.nuspec'):
        dependencies = parse_nuspec_file(filepath=filepath, logger=logger)
    elif filepath.endswith('.csproj'):
        dependencies = parse_csproj_file(filepath=filepath, logger=logger)

    return dependencies


if __name__ == "__main__":

    import logging
    from core.log import Logger

    packages_config_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/c#/NugetUpdater/NugetUpdater/packages.config'
    nuspec_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/c#/NuspecGraph/NuspecGraph/test.nuspec'
    csproj_location = '/Users/rongdang/Desktop/sca-2.0/extracted_folder/c#/nuspec-lsp/src/NuSpec.Server/NuSpec.Server.csproj'
    log = Logger(path='../../log_dir/nuget_projects.log', cmd_level=logging.INFO, file_level=logging.ERROR)

    dep_result = list()
    # nuget_deps = parse_nuget_files(filepath=packages_config_location, logger=log)
    # nuget_deps = parse_nuget_files(filepath=nuspec_location, logger=log)
    nuget_deps = parse_nuget_files(filepath=csproj_location, logger=log)

    dep_result.extend(nuget_deps)
    if dep_result:
        print(len(dep_result))
        for dep in dep_result:
            print(dep)
