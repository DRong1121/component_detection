import re
import os
import xml
import xml.etree.ElementTree as ET

namespace = '{http://maven.apache.org/POM/4.0.0}'


def parse_version_str(version):
    item_pattern = r'[\[\(][0-9,.]+[\)\]]'
    match_result = re.findall(item_pattern, version)
    if match_result:
        item_list = list()
        for match_item in match_result:
            if match_item.startswith('[') and match_item.endswith(']'):
                inner_str = match_item.lstrip('[').rstrip(']')
                nums = inner_str.split(',')
                if len(nums) == 1:
                    version_item = nums[0].strip()
                else:
                    version_item = '>=' + nums[0].strip() + ', ' + '<=' + nums[-1].strip()
                item_list.append(version_item)
                continue
            elif match_item.startswith('(') and match_item.endswith(')'):
                inner_str = match_item.lstrip('(').rstrip(')')
                if inner_str.startswith(','):
                    version_item = '<' + inner_str.lstrip(',')
                elif inner_str.endswith(','):
                    version_item = '>' + inner_str.rstrip(',')
                else:
                    nums = inner_str.split(',')
                    version_item = '>' + nums[0].strip() + ', ' + '<' + nums[-1].strip()
                item_list.append(version_item)
                continue
            elif match_item.startswith('[') and match_item.endswith(')'):
                inner_str = match_item.lstrip('[').rstrip(')')
                nums = inner_str.split(',')
                if '' in nums:
                    version_item = '>=' + nums[0].strip()
                else:
                    version_item = '>=' + nums[0].strip() + ', ' + '<' + nums[-1].strip()
                item_list.append(version_item)
                continue
            elif match_item.startswith('(') and match_item.endswith(']'):
                inner_str = match_item.lstrip('(').rstrip(']')
                nums = inner_str.split(',')
                if '' in nums:
                    version_item = '<=' + nums[-1].strip()
                else:
                    version_item = '>' + nums[0].strip() + ', ' + '<=' + nums[-1].strip()
                item_list.append(version_item)
        version_str = ', '.join(item_list)
        return version_str
    else:
        return version


def get_pom_file_tree(filepath, logger):
    """
       desc: 获取当前pom文件的element tree
       params: filepath: str, 当前pom文件所在路径
       return: tree: ElementTree, pom文件加载后的返回值
    """
    try:
        tree = ET.ElementTree(file=filepath)
        return tree
    except Exception as e:
        logger.error('Exception occurs when loading pom.xml file {}: {}'.format(filepath, str(e)))
        return None


def get_parent_filepath(tree, current_filepath):
    """
       desc: 获取当前pom文件的parent filepath
       params: tree: ElementTree, 当前pom ElementTree;
               current_filepath: str, 当前pom文件所在路径
       return: parent_filepath: str, 当前pom文件的parent filepath
    """
    relative_path_node = tree.find('./' + namespace + 'parent' + '/' + namespace + 'relativePath')
    if isinstance(relative_path_node, xml.etree.ElementTree.Element):
        relative_path = relative_path_node.text
        file_dir = os.path.split(current_filepath)[0]
        if relative_path:
            for i in range(0, relative_path.count('..'+os.sep)):
                file_dir = os.path.split(file_dir)[0]
            parent_filepath = os.path.join(file_dir, relative_path.split('..'+os.sep)[-1])
        else:
            parent_filepath = ''
    else:
        parent_filepath = os.path.join(str(os.path.split(os.path.split(current_filepath)[0])[0]), 'pom.xml')
    return parent_filepath


def get_property_by_tag(filepath, tag, logger):
    """
       desc: 递归寻找tag=${search_tag}对应的属性标签的值
       params: filepath: str, 当前pom文件所在路径;
               tag: str, 需要寻找的属性标签
       return: property_value: str 属性标签的值
    """
    search_tag = tag.strip('$').strip('{').strip('}')
    search_tag = search_tag.split('project.')[-1]
    property_value = ''

    tree = get_pom_file_tree(filepath=filepath, logger=logger)
    if tree:
        node = tree.find('.//' + namespace + search_tag)
        if isinstance(node, xml.etree.ElementTree.Element):
            property_value = node.text
            return property_value
        else:
            parent_filepath = get_parent_filepath(tree=tree, current_filepath=filepath)
            if parent_filepath and os.path.exists(parent_filepath):
                property_value = get_property_by_tag(filepath=parent_filepath, tag=tag, logger=logger)

    return property_value


def get_version_by_inherit_pom_file(parent_filepath, groupid, artifactid, logger):
    """
       desc: 递归寻找groupid, artifactid对应的项目版本号version
       params: filepath: str, 当前pom文件所在路径;
               groupid: str, 项目groupid的值;
               artifactid: str, 项目artifactid的值
       return: version: str, 项目版本号
    """
    version = ''

    parent_tree = get_pom_file_tree(filepath=parent_filepath, logger=logger)
    if parent_tree:
        dependencyManagement = parent_tree.find('./' + namespace + 'dependencyManagement')
        if isinstance(dependencyManagement, xml.etree.ElementTree.Element):
            for dependencies in dependencyManagement:
                for dependency in dependencies:
                    temp = dict()
                    temp['groupId'] = ''
                    temp['artifactId'] = ''

                    for child in dependency:
                        key = child.tag.split(namespace)[-1]
                        value = child.text
                        # 没有考虑groupId, artifactId的值以$开头的情况
                        if key == 'groupId' and value == groupid:
                            temp['groupId'] = groupid
                            continue
                        elif key == 'artifactId' and value == artifactid:
                            temp['artifactId'] = artifactid
                            continue
                        elif key == 'version' and temp['groupId'] and temp['artifactId']:
                            if not value.startswith('$'):
                                try:
                                    version = parse_version_str(version=value)
                                except Exception as e:
                                    logger.error('Exception occurs in function parse_version_str '
                                                 'when parsing pom.xml on {}: {}'.format(parent_filepath, str(e)))
                                    version = ''
                            else:
                                version = get_property_by_tag(filepath=parent_filepath, tag=value, logger=logger)
                            return version
        else:
            parent_filepath = get_parent_filepath(tree=parent_tree, current_filepath=parent_filepath)
            if parent_filepath and os.path.exists(parent_filepath):
                version = get_version_by_inherit_pom_file(parent_filepath=parent_filepath,
                                                          groupid=groupid, artifactid=artifactid, logger=logger)

    return version


def get_import_pom_file_gav(tree):
    """
       desc: 获取当前pom ElementTree的dependencyManagement标签中，import的pom文件的G(groupId)A(artifactId)V(version)三元组
       params: tree: ElementTree, 当前pom ElementTree;
       return: gav_result: list, 当前pom ElementTree import的pom文件GAV三元组列表
               e.g.
               [
                 {
                    'groupId': 'com.juvenxu.sample',
                    'artifactId': 'sample-dependency-infrastructure',
                    'version': '1.0-SNAPSHOT'
                 },
                 ...
               ]
    """
    gav_result = list()

    dependencyManagement = tree.find('./' + namespace + 'dependencyManagement')
    if isinstance(dependencyManagement, xml.etree.ElementTree.Element):
        for dependencies in dependencyManagement:
            for dependency in dependencies:
                temp = dict()
                temp['groupId'] = ''
                temp['artifactId'] = ''
                temp['version'] = ''
                flag = False

                for child in dependency:
                    key = child.tag.split(namespace)[-1]
                    value = child.text
                    if key == 'groupId':
                        temp['groupId'] = value
                        continue
                    elif key == 'artifactId':
                        temp['artifactId'] = value
                        continue
                    elif key == 'version':
                        temp['version'] = value
                        continue
                    elif key == 'scope':
                        if value == 'import':
                            flag = True

                if temp['groupId'] and temp['artifactId'] and temp['version'] and flag:
                    gav_result.append(temp)

    return gav_result


def get_version_by_import_pom_file(search_result, gav_result, groupid, artifactid, logger):
    """
       desc: 遍历寻找groupid, artifactid对应的项目的版本号version
       params: search_result: list, 项目的配置文件四元组列表;
               gav_result: list, 当前pom ElementTree import的pom文件GAV三元组列表;
               groupid: str, 项目groupid的值;
               artifactid: str, 项目artifactid的值
       return: version: str, 项目版本号
    """
    version = ''

    for file_item in search_result:
        if file_item['file_name'] == 'pom.xml':
            tree = get_pom_file_tree(filepath=file_item['file_path_absolute'], logger=logger)
            if tree:
                project_gav = dict()
                parent_node = tree.find('./' + namespace + 'parent')
                if isinstance(parent_node, xml.etree.ElementTree.Element):
                    project_gav['groupId'] = tree.find('./' + namespace + 'parent' + '/' + namespace + 'groupId').text
                    project_gav['version'] = tree.find('./' + namespace + 'parent' + '/' + namespace + 'version').text
                else:
                    project_gav['groupId'] = tree.find('./' + namespace + 'groupId').text
                    project_gav['version'] = tree.find('./' + namespace + 'version').text
                project_gav['artifactId'] = tree.find('./' + namespace + 'artifactId').text

                if project_gav in gav_result:
                    dependencyManagement = tree.find('./' + namespace + 'dependencyManagement')
                    if isinstance(dependencyManagement, xml.etree.ElementTree.Element):
                        for dependencies in dependencyManagement:
                            for dependency in dependencies:
                                temp = dict()
                                temp['groupId'] = ''
                                temp['artifactId'] = ''

                                for child in dependency:
                                    key = child.tag.split(namespace)[-1]
                                    value = child.text
                                    # 没有考虑groupId, artifactId的值以$开头的情况
                                    if key == 'groupId' and value == groupid:
                                        temp['groupId'] = groupid
                                        continue
                                    elif key == 'artifactId' and value == artifactid:
                                        temp['artifactId'] = artifactid
                                        continue
                                    elif key == 'version' and temp['groupId'] and temp['artifactId']:
                                        if not value.startswith('$'):
                                            try:
                                                version = parse_version_str(version=value)
                                            except Exception as e:
                                                logger.error('Exception occurs in function parse_version_str '
                                                             'when parsing pom.xml on {}: {}'.format(
                                                              file_item['file_path_absolute'], str(e)))
                                                version = ''
                                        else:
                                            version = get_property_by_tag(filepath=file_item['file_path_absolute'],
                                                                          tag=value, logger=logger)
                                        return version

    return version


def parse_maven_pom_file(filepath, search_result, logger):

    dep_result = list()

    tree = get_pom_file_tree(filepath=filepath, logger=logger)
    if tree:
        dependencies = tree.find('./' + namespace + 'dependencies')
        if isinstance(dependencies, xml.etree.ElementTree.Element):
            for dependency in dependencies:
                item = dict()
                item['type'] = 'maven'
                item['namespace'] = ''
                item['name'] = ''
                item['version'] = ''
                item['language'] = 'Java'

                for child in dependency:
                    key = child.tag.split(namespace)[-1]
                    value = child.text.strip('\n').strip()
                    if key == 'groupId':
                        if '$' not in value:
                            item['namespace'] = value
                        else:
                            namespace_str = value.split('$')
                            for i in range(0, len(namespace_str)):
                                if namespace_str[i].startswith('{') and namespace_str[i].startswith('}'):
                                    namespace_str[i] = get_property_by_tag(filepath=filepath, tag=namespace_str[i],
                                                                           logger=logger).strip('\n').strip()
                            item['namespace'] = ''.join(namespace_str)
                        continue
                    elif key == 'artifactId':
                        if '$' not in value:
                            item['name'] = value
                        else:
                            name_str = value.split('$')
                            for i in range(0, len(name_str)):
                                if name_str[i].startswith('{') and name_str[i].endswith('}'):
                                    name_str[i] = get_property_by_tag(filepath=filepath, tag=name_str[i],
                                                                      logger=logger).strip('\n').strip()
                            item['name'] = ''.join(name_str)
                        continue
                    elif key == 'version':
                        if '$' not in value:
                            try:
                                item['version'] = parse_version_str(version=value)
                            except Exception as e:
                                logger.error('Exception occurs in function parse_version_str '
                                             'when parsing pom.xml on {}: {}'.format(filepath, str(e)))
                                item['version'] = ''
                        else:
                            version_str = value.split('$')
                            for i in range(0, len(version_str)):
                                if version_str[i].startswith('{') and version_str[i].endswith('}'):
                                    version_str[i] = get_property_by_tag(filepath=filepath, tag=version_str[i],
                                                                         logger=logger).strip('\n').strip()
                            item['version'] = ''.join(version_str)

                if item['namespace'] and item['name'] and not item['version']:
                    # 获取当前pom文件的dependencyManagement标签中的import pom文件GAV三元组列表
                    gav_result = get_import_pom_file_gav(tree=tree)
                    if gav_result:
                        # 根据import pom文件获取依赖版本号
                        item['version'] = get_version_by_import_pom_file(search_result=search_result,
                                                                         gav_result=gav_result,
                                                                         groupid=item['namespace'],
                                                                         artifactid=item['name'], logger=logger)
                    # 根据pom文件继承关系获取依赖版本号
                    if not item['version']:
                        parent_filepath = get_parent_filepath(tree=tree, current_filepath=filepath)
                        if parent_filepath and os.path.exists(parent_filepath):
                            item['version'] = get_version_by_inherit_pom_file(parent_filepath=parent_filepath,
                                                                              groupid=item['namespace'],
                                                                              artifactid=item['name'], logger=logger)

                if item['namespace'] and item['name']:
                    item['name'] = item['namespace'] + '/' + item['name']
                    dep_result.append(item)

    return dep_result


if __name__ == "__main__":

    # filepath = '/Users/rongdang/Desktop/sca-2.0/core/file_parsers/test/maven_test_2/core/pom.xml'
    # search_result = []
    #
    # dep_result = parse_pom_file(filepath=filepath, search_result=search_result)
    # for item in dep_result:
    #     print(item)

    version_str = '(,1.0]'
    split_str = version_str.lstrip('(').rstrip(']').split(',')
    if '' in split_str:
        print(split_str[-1])
