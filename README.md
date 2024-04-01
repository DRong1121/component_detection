# Open-Source Software Component Detection

Open-Source Toolkits：  
1. dependency-check  
   Homepage: https://github.com/jeremylong/DependencyCheck  
   File Analyzers: https://jeremylong.github.io/DependencyCheck/analyzers/index.html  
   CLI Params: https://jeremylong.github.io/DependencyCheck/dependency-check-cli/arguments.html  
   Analyzer Code: https://github.com/jeremylong/DependencyCheck/tree/main/core/src/main/java/org/owasp/dependencycheck/analyzer  
2. scancode  
   Homepage: https://github.com/nexB/scancode-toolkit  
   Package Code: https://github.com/nexB/scancode-toolkit/tree/develop/src/packagedcode

Commercial Toolkit：  
1. Synopsys Black Duck   
   Detectors: https://community.synopsys.com/s/document-item?bundleId=integrations-detect&topicId=components%2Fdetectors.html&_LANG=enus   
   Package Managers:  https://community.synopsys.com/s/document-item?bundleId=integrations-detect&topicId=packagemgrs%2Foverview.html&_LANG=enus  

Our Toolkit：
1. Pre-prepared Tools:  
   1）jdk-11.0.1_linux-x64_bin.tar.gz (https://www.oracle.com/hk/java/technologies/javase/jdk11-archive-downloads.html): download to the docker directory  
   2）apache-maven-3.8.6-bin.tar.gz (https://maven.apache.org/download.cgi): download to the docker directory  
   3）gradle-6.8.2-bin.zip (https://gradle.org/releases/): download to the docker directory  
   4）flutter_linux_3.0.5-stable.tar.xz (https://docs.flutter.dev/development/tools/sdk/releases?tab=linux) : download to the docker directory  
   5）swift-5.7-RELEASE-ubuntu20.04.tar.gz (https://www.swift.org/download/): download to the docker directory  
   6）rebar3 (https://github.com/erlang/rebar3): download, rename to 'rebar3' in the docker directory  
2. Setup the Running and Compilation Environment:  
   Install docker, run command `cd component_detection/docker`  
   1）run command `docker build . -t sca_env:release`  
   2）run command `docker run --name sca -it sca_env:release`  
   3）run command `docker exec -it sca /bin/bash`  
3. Use the Toolkit:  
   1) Start and execute the 'sca' container  
   2) Copy the 'core' directory to the 'home' directory in the 'sca' container(using the `docker cp` command)  
   3) Run the following command once  
   `find /home/core/executables -type f -print0 | xargs -0 dos2unix --`  
   4) Run the command `cd /home/core`, the following command is an example of the toolkit execution  
   `python3 scan.py -is_output=True -output_dir='../check_result' -check_dir='../extracted_folder/axios-0.19.2' -is_build=True -search_depth=1 -is_skip=False`  
   5) Execution parameters   
   | Parameter Name      | Parameter Type     | Required      | Description               |   
   | :---------- | :---------- | :---------- | :-------------------- |     
   | check_dir   | string      | True           | 待测项目所在路径        |  
   | is_output   | bool        | False           | 是否以JSON文件形式输出检测结果，默认为False |    
   | output_dir  | string      | False           | 检测结果所在路径，默认为‘../check_result’ |    
   | is_build    | bool        | False           | 是否编译构建项目，默认为False             |   
   | is_skip     | bool        | False           | 是否跳过devDependencies，默认为False     |  
   | search_depth| int         | False           | 搜索深度，默认为3       |    
   Other instructions:  
   1）check_dir为项目文件所在路径（建议使用绝对路径），不支持压缩文件检测。   
   2）is_build仅针对Bundler, Cargo, Composer, Conan, Cpan, Dart, Go, Gradle, Leiningen, Maven, Mix, NPM, Rebar3, Sbt, Stack和Swift管理的项目可以设置为True。   
   3）is_skip仅针对Composer, Dart和NPM管理的项目可进行设置。  
   4）当前检测功能仅支持Gradle管理的Java项目，不支持Andorid项目。  
4. Supported Languages and Detection Types：   
   | No.        | Language       | Detection Type      |  Config Files      | Package Managers     | 是否自研      |   
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
