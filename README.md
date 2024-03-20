# sca-2.0

Software Component Analysis (SCA) 软件成分分析

开源工具：  
1. dependency-check  
   Homepage: https://github.com/jeremylong/DependencyCheck  
   File Analyzers: https://jeremylong.github.io/DependencyCheck/analyzers/index.html  
   CLI Params: https://jeremylong.github.io/DependencyCheck/dependency-check-cli/arguments.html  
   Analyzer Code: https://github.com/jeremylong/DependencyCheck/tree/main/core/src/main/java/org/owasp/dependencycheck/analyzer  
   
2. scancode  
   Homepage: https://github.com/nexB/scancode-toolkit  
   Package Code: https://github.com/nexB/scancode-toolkit/tree/develop/src/packagedcode

商用工具：  
1. Synopsys Black Duck   
   Detectors: https://community.synopsys.com/s/document-item?bundleId=integrations-detect&topicId=components%2Fdetectors.html&_LANG=enus   
   Package Managers:  https://community.synopsys.com/s/document-item?bundleId=integrations-detect&topicId=packagemgrs%2Foverview.html&_LANG=enus  

自研工具：
1. Pre-prepared Tools:  
   1）jdk-11.0.1_linux-x64_bin.tar.gz (https://www.oracle.com/hk/java/technologies/javase/jdk11-archive-downloads.html) ：下载后放置在docker目录下  
   2）apache-maven-3.8.6-bin.tar.gz (https://maven.apache.org/download.cgi) ：下载后放置在docker目录下  
   3）gradle-6.8.2-bin.zip (https://gradle.org/releases/) ：下载后放置在docker目录下  
   4）flutter_linux_3.0.5-stable.tar.xz (https://docs.flutter.dev/development/tools/sdk/releases?tab=linux) ：下载后放置在docker目录下  
   5）swift-5.7-RELEASE-ubuntu20.04.tar.gz (https://www.swift.org/download/) ：下载后放置在docker目录下  
   6）rebar3 (https://github.com/erlang/rebar3) ：下载后解压，将解压后的目录(重命名为rebar3)放置在docker目录下  
2. 运行&编译环境创建:  
   自行安装docker，进入到本项目的docker目录下  
   1）运行`docker build . -t sca_env:release`命令创建基础环境镜像  
   2）运行`docker run --name sca -it sca_env:release`命令创建容器  
   3）运行`docker exec -it sca /bin/bash`命令运行容器  
3. 功能模块调用：  
   启动运行sca容器，将本项目的core目录拷贝至容器中的/home目录下，并执行命令（仅一次）  
   `find /home/core/executables -type f -print0 | xargs -0 dos2unix --`  
   进入到/home/core目录下，运行命令（示例）   
   `python3 scan.py -is_output=True -output_dir='../check_result' -check_dir='../extracted_folder/axios-0.19.2' -is_build=True -search_depth=1 -is_skip=False`  
   参数说明  
   | 参数名称      | 参数类型     | 是否必选      | 参数描述               |   
   | :---------- | :---------- | :---------- | :-------------------- |     
   | check_dir   | string      | 是           | 待测项目所在路径        |  
   | is_output   | bool        | 否           | 是否以JSON文件形式输出检测结果，默认为False |    
   | output_dir  | string      | 否           | 检测结果所在路径，默认为‘../check_result’ |    
   | is_build    | bool        | 否           | 是否编译构建项目，默认为False             |   
   | is_skip     | bool        | 否           | 是否跳过devDependencies，默认为False     |  
   | search_depth| int         | 否           | 搜索深度，默认为3       |    
   
   其他说明  
   1）check_dir为项目文件所在路径（建议使用绝对路径），不支持压缩文件检测。   
   2）is_build仅针对Bundler, Cargo, Composer, Conan, Cpan, Dart, Go, Gradle, Leiningen, Maven, Mix, NPM, Rebar3, Sbt, Stack和Swift管理的项目可以设置为True。   
   3）is_skip仅针对Composer, Dart和NPM管理的项目可进行设置。  
   4）当前检测功能仅支持Gradle管理的Java项目，不支持Andorid项目。  
   
   结果示例  
   ![检测结果JSON文件](https://git.vulgraph.net:8000/dangrong/sca-2.0/-/blob/main/result.png "result")  
   dep_result列表（依赖项条目列表）字段说明  
     •  type: 包管理器类型 (required)  
     •  namespace: 依赖项名称前缀 (optional)  
     •  name: 依赖项名称 (required)  
     •  version: 依赖项版本 (optional)  
     •  language: 依赖项语言 (required)  
   
4. 当前功能模块支持的语言种类及检测模式：   
   | 序号        | 语言       | 检测模式      |  配置文件      | 包管理器     | 是否自研      |   
   | :---------- | :---------- | :---------- | :-------------------- | :---------- | :---------- |  
   | 1           | C/C++       | 编译、非编译   | conanfile.py, conan.lock | conan | 是     |   
   | 2           | C#          | 非编译        | packages.config, *.csproj, *.nuspec  | - | 是     |   
   | 3           | Clojure     | 编译、非编译   | project.clj | lein | 是     |  
   | 4           | Dart        | 编译、非编译   | pubspec.yaml, pubspec.lock | dart/flutter | 是     |  
   | 5           | Elixir      | 编译、非编译   | mix.exs, mix.lock | mix | 是     |  
   | 6           | Erlang      | 编译、非编译   | rebar.config | rebar3 | 是     |  
   | 7           | Golang      | 编译、非编译   | go.mod, go.sum, Godeps.json, Gopkg.lock | go | 是 |  
   | 8           | Haskell     | 编译、非编译   | stack.yaml, package.yaml, <package_name>.cabal | stack | 是 |  
   | 9           | Java        | 编译、非编译   | pom.xml, build.gradle | maven, gradle | 是     |  
   | 10          | Node JS     | 编译、非编译   | package.json, package-lock.json, npm-shrinkwrap.json, pnpm-lock.yaml, yarn.lock | npm | 是 |  
   | 11          | Objective C | 非编译        | Podfile, Podfile.lock, *.podspec, Cartfile, Cartfile.resolved | - | 是     |  
   | 12          | Perl        | 编译、非编译   | Makefile.PL, Build.PL, cpanfile | cpanm | 是     |  
   | 13          | PHP         | 编译、非编译   | composer.json, composer.lock | composer | 是     |  
   | 14          | Python      | 非编译        | environment.yml, setup.py, requirements.txt, Pipfile, Pipfile.lock, pyproject.toml, poetry.lock | - | 是     |   
   | 15          | R           | 非编译        | DESCRIPTION, packrat.lock | - | 是     |   
   | 16          | Ruby        | 编译、非编译   | Gemfile, Gemfile.lock, *.gemspec | gem, bundler | 是     |   
   | 17          | Rust        | 编译、非编译   | Cargo.toml, Cargo.lock | cargo | 是     |   
   | 18          | Scala       | 编译、非编译   | build.sbt, Dependencies.scala  | sbt, plugin: sbt-dependency-graph | 是     |   
   | 19          | Swift       | 编译、非编译   | Package.swift, Package.resolved  | swift | 是     |  