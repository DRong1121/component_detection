import os
import sys
import subprocess
import argparse
import logging
from datetime import datetime

sys.path.append('.')
sys.path.append('..')
from config import Config as cf
from detect import construct_candidate_file_list
from build import build_with_scripts
from parse import parse_temp_file
from core.file_parsers.file_parsers import parse_config_files
from util import parse_check_result, write_check_result, read_log
from log import Logger


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('invalid boolean value: \'' + str(v) + '\'')


def set_config(is_build, is_skip, search_depth, is_output, output_dir):
    cf.is_build = is_build
    cf.is_skip = is_skip
    cf.search_depth = search_depth
    cf.is_output = is_output
    cf.output_dir = output_dir


class Scanning(object):
    def __init__(self, check_dir, config, curr_time):

        # self._tool_dir = os.path.join(config.scanning_dir, 'dependency-check', 'bin', 'dependency-check.sh')
        self._scan_dir = os.path.abspath(path=check_dir)
        self._root_name = os.path.split(check_dir)[-1]

        self._is_build = config.is_build
        self._is_skip = config.is_skip
        self._search_depth = config.search_depth
        self._is_output = config.is_output
        self._output_dir = config.output_dir

        self._log_dir = config.log_dir
        self._log_file_name = self._root_name + '__' + curr_time + '.log'
        self._log_file_path = os.path.join(self._log_dir, self._log_file_name)

        # self._temp_dir = config.temp_dir
        # self._temp_file_name = self._root_name + '__' + curr_time + '.json'
        # self._temp_file_path = os.path.join(self._temp_dir, self._temp_file_name)

        if self._is_output:
            self._check_result_dir = os.path.abspath(path=self._output_dir)
            if self._is_build:
                self._check_result_file_name = 'dep-check__' + self._root_name + '__build' + '__' + curr_time + '.json'
            else:
                self._check_result_file_name = 'dep-check__' + self._root_name + '__buildless' + '__' + curr_time + '.json'
            self._check_result_file_path = os.path.join(self._check_result_dir, self._check_result_file_name)

        self._search_result = None
        self._build_result = None
        self._dep_result = None
        # self._parse_result = None
        self._init_dirs()
        self.logger = Logger(path=self._log_file_path, cmd_level=logging.INFO, file_level=logging.WARN)

    def _init_dirs(self):
        if not os.path.exists(self._log_dir):
            os.makedirs(self._log_dir)
        # if not os.path.exists(self._temp_dir):
        #     os.makedirs(self._temp_dir)
        if self._is_output and (not os.path.exists(self._check_result_dir)):
            os.makedirs(self._check_result_dir)

    def _delete_temp_result_files(self):
        if os.path.exists(self._temp_file_path):
            os.remove(self._temp_file_path)

    def scan(self):
        self.logger.info('[+] Start the scanning process...')
        if os.path.exists(self._scan_dir):
            self.logger.info('[+] Start detecting candidate config files...')
            self._search_result = construct_candidate_file_list(scan_dir=self._scan_dir, root_name=self._root_name,
                                                                search_depth=self._search_depth, logger=self.logger)

            # STEP 1: build the project --> build_result
            if self._search_result and self._is_build:
                self.logger.info('[+] Start building the project using scripts...')
                self._build_result = build_with_scripts(scan_dir=self._scan_dir, search_result=self._search_result,
                                                        logger=self.logger)

            # STEP 2: Dependency Check toolkit --> dep_result
            # TODO:  删除Dependency Check工具调用
            # self.logger.info('[+] Start executing dependency check toolkit...')
            # temp_json_path = self.dep_check()
            # if temp_json_path:
            #     self.logger.info('[+] Start parsing dependency check result file: ' + self._temp_file_path)
            #     self._dep_result = parse_temp_file(temp_file_path=temp_json_path, logger=self.logger)
            # else:
            #     self.logger.error('Subprocess failure: dependency-check toolkit execution failed!')

            # STEP 3: parse config files --> dep_result
            if self._search_result:
                self.logger.info('[+] Start parsing config files...')
                self._dep_result = parse_config_files(scan_dir=self._scan_dir, root_name=self._root_name,
                                                      is_skip=self._is_skip, is_build=self._is_build,
                                                      build_result=self._build_result,
                                                      search_result=self._search_result, logger=self.logger)

            # STEP 4: parse dep_result
            self.logger.info('[+] Start parsing dep result...')
            self._dep_result = parse_check_result(dep_result=self._dep_result)

            # STEP 5: delete temp result files
            # self.logger.info('[+] Start deleting temp result file: ' + self._temp_file_path)
            # self._delete_temp_result_files()

            # STEP 6: write search_result, build_result, dep_result to json file (optional)
            if self._is_output:
                self.logger.info('[+] Start writing result to file: ' + self._check_result_file_path)
                write_check_result(result_file_path=self._check_result_file_path, search_result=self._search_result,
                                   build_result=self._build_result, dep_result=self._dep_result)

        else:
            self.logger.error('Subprocess failure: project directory: {} does not exist!'.format(self._scan_dir))

        # Final step: return check result
        success, result, message = self.get_dep_check_result()
        self.logger.info('[+] Scanning process done.')
        return success, result, message

    def dep_check(self):
        command = self._tool_dir + " --out " + self._temp_file_path + " --scan " + self._scan_dir + \
                  " --format JSON --enableExperimental --noupdate" \
                  " --disableOssIndex --disableOssIndexCache --disableRetireJS --disableNodeJS" \
                  " --disableNodeAudit --disableNodeAuditCache --disablePnpmAudit --disableYarnAudit" \
                  " --disableCocoapodsAnalyzer --disableComposer --disableCmake --disableCpan --disableGolangDep" \
                  " --disableGolangMod --disableMixAudit --disableMSBuild --disableNuspec --disableNugetconf" \
                  " --disablePyDist --disablePyPkg --disablePip --disablePipfile" \
                  " --disableRubygems --disableBundleAudit" \
                  " --disableSwiftPackageManagerAnalyzer --disableSwiftPackageResolvedAnalyzer"
        # if self._is_skip:
        #     command = command + ' --nodePackageSkipDevDependencies --nodeAuditSkipDevDependencies'
        command_params = command.split()
        p = subprocess.Popen(command_params, shell=False)
        p.communicate()
        returncode = p.returncode
        if returncode == 0:
            return self._temp_file_path
        if returncode != 0:
            if os.path.exists(self._temp_file_path):
                return self._temp_file_path
            else:
                return None

    def get_dep_check_result(self):

        result = self._dep_result if self._dep_result else list()
        error_info = read_log(log_file_path=self._log_file_path)
        if not error_info:
            success = True
            message = '[INFO] Succeed.'
        else:
            if result:
                success = True
                message = '[INFO] Partial Succeed.\n' + error_info
            else:
                success = False
                message = '[INFO] Failure.\n' + error_info

        return success, result, message


def scan_api(check_dir, output_dir, search_depth=3, is_build=False, is_skip=False, is_output=False):
    try:
        set_config(search_depth=search_depth, is_build=is_build, is_skip=is_skip,
                   is_output=is_output, output_dir=output_dir)
        current_time = datetime.now().strftime('%Y_%m_%d_%H_%M_%S').__str__()
        scanning = Scanning(check_dir=check_dir, config=cf, curr_time=current_time)
        success, result, message = scanning.scan()
    except Exception as e:
        success, result, message = False, list(), str(e)
    return success, result, message


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-check_dir', required=True, type=str)
    parser.add_argument('-is_build', default=False, required=False, type=str2bool)
    parser.add_argument('-is_skip', default=False, required=False, type=str2bool)
    parser.add_argument('-search_depth', default=3, required=False, type=int)
    parser.add_argument('-is_output', default=False, required=False, type=str2bool)
    parser.add_argument('-output_dir', default='../check_result', required=False, type=str)
    args_cmd = parser.parse_args()

    success, result, message = scan_api(check_dir=args_cmd.check_dir, search_depth=args_cmd.search_depth,
                                        is_build=args_cmd.is_build, is_skip=args_cmd.is_skip,
                                        is_output=args_cmd.is_output, output_dir=args_cmd.output_dir)

    if args_cmd.is_output:
        print('------------------------------------------------------------')
        print('Success: ' + str(success))
        print('Dep item nums: ' + str(len(result)))
        print(message)
        print('------------------------------------------------------------')
    else:
        print('------------------------------------------------------------')
        print('Success: ' + str(success))
        print(message)
        print('Dep item nums: ' + str(len(result)))
        if result:
            for item in result:
                print(item)
        print('------------------------------------------------------------')
