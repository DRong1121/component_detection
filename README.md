## Open-Source Software Component Detection

### Open-Source Toolkits：  
1. dependency-check  
   Homepage: https://github.com/jeremylong/DependencyCheck  
   File Analyzers: https://jeremylong.github.io/DependencyCheck/analyzers/index.html  
   CLI Params: https://jeremylong.github.io/DependencyCheck/dependency-check-cli/arguments.html  
   Analyzer Code: https://github.com/jeremylong/DependencyCheck/tree/main/core/src/main/java/org/owasp/dependencycheck/analyzer  
2. scancode  
   Homepage: https://github.com/nexB/scancode-toolkit  
   Package Code: https://github.com/nexB/scancode-toolkit/tree/develop/src/packagedcode

### Commercial Toolkit：  
1. Synopsys Black Duck   
   Detectors: https://community.synopsys.com/s/document-item?bundleId=integrations-detect&topicId=components%2Fdetectors.html&_LANG=enus   
   Package Managers:  https://community.synopsys.com/s/document-item?bundleId=integrations-detect&topicId=packagemgrs%2Foverview.html&_LANG=enus  

### Our Toolkit：
1. Pre-prepared Tools:  
   1）jdk-11.0.1_linux-x64_bin.tar.gz (https://www.oracle.com/hk/java/technologies/javase/jdk11-archive-downloads.html): download to the docker directory  
   2）apache-maven-3.8.6-bin.tar.gz (https://maven.apache.org/download.cgi): download to the docker directory  
   3）gradle-6.8.2-bin.zip (https://gradle.org/releases/): download to the docker directory  
   4）flutter_linux_3.0.5-stable.tar.xz (https://docs.flutter.dev/development/tools/sdk/releases?tab=linux) : download to the docker directory  
   5）swift-5.7-RELEASE-ubuntu20.04.tar.gz (https://www.swift.org/download/): download to the docker directory  
   6）rebar3 (https://github.com/erlang/rebar3): download, rename to 'rebar3' in the docker directory  
2. Setup the Running and Compilation Environment:  
   Install docker, run command `cd software_component_detection/docker`  
   1）run command `docker build . -t sca_env:release`  
   2）run command `docker run --name sca -it sca_env:release`  
   3）run command `docker exec -it sca /bin/bash`  
3. Use the Toolkit:  
   1）Start and execute the 'sca' container  
   2）Copy the 'core' directory to the 'home' directory in the 'sca' container (using the `docker cp` command)  
   3）Run the following command once  
   `find /home/core/executables -type f -print0 | xargs -0 dos2unix --`  
   4）Run the command `cd /home/core`, the following command is an example of the toolkit execution command    
   `python3 scan.py -is_output=True -output_dir='../check_result' -check_dir='../extracted_folder/axios-0.19.2' -is_build=True -search_depth=1 -is_skip=False`  
   5）Execution parameters   
   | Parameter Name      | Parameter Type     | Is Required      | Description               |   
   | :---------- | :---------- | :---------- | :-------------------- |     
   | check_dir   | string      | True            | Input project directory path (recommend the absolute file path) |  
   | is_output   | bool        | False           | Whether to write the check result into JSON file, default: False|    
   | output_dir  | string      | False           | Output result root directory, default: ‘../check_result’        |    
   | is_build    | bool        | False           | Whether to build the project, default: False               |   
   | is_skip     | bool        | False           | Whether to skip devDependencies, default: False            |  
   | search_depth| int         | False           | Search depth, default: 3 (root search depth == 0)          |
   
   6）Output result (demo) [result.png](https://github.com/DRong1121/software_component_detection/tree/main/result.png)

4. Supported Languages and Detection Types：   
   | No.        | Language       | Detection Mode(s)      |  Config File(s)      | Package Manager(s)     |   
   | :---------- | :---------- | :---------- | :-------------------- | :---------- |  
   | 1           | C/C++       | Build, Buildless   | conanfile.py, conan.lock | conan |   
   | 2           | C#          | Buildless          | packages.config, *.csproj, *.nuspec  | - |   
   | 3           | Clojure     | Build, Buildless   | project.clj | lein |  
   | 4           | Dart        | Build, Buildless   | pubspec.yaml, pubspec.lock | dart/flutter |  
   | 5           | Elixir      | Build, Buildless   | mix.exs, mix.lock | mix |  
   | 6           | Erlang      | Build, Buildless   | rebar.config | rebar3 |  
   | 7           | Golang      | Build, Buildless   | go.mod, go.sum, Godeps.json, Gopkg.lock | go |  
   | 8           | Haskell     | Build, Buildless   | stack.yaml, package.yaml, <package_name>.cabal | stack |  
   | 9           | Java        | Build, Buildless   | pom.xml, build.gradle | maven, gradle |  
   | 10          | Node JS     | Build, Buildless   | package.json, package-lock.json, npm-shrinkwrap.json, pnpm-lock.yaml, yarn.lock | npm |  
   | 11          | Objective C | Buildless          | Podfile, Podfile.lock, *.podspec, Cartfile, Cartfile.resolved | - |  
   | 12          | Perl        | Build, Buildless   | Makefile.PL, Build.PL, cpanfile | cpanm |  
   | 13          | PHP         | Build, Buildless   | composer.json, composer.lock | composer |  
   | 14          | Python      | Buildless          | environment.yml, setup.py, requirements.txt, Pipfile, Pipfile.lock, pyproject.toml, poetry.lock | - |   
   | 15          | R           | Buildless          | DESCRIPTION, packrat.lock | - |   
   | 16          | Ruby        | Build, Buildless   | Gemfile, Gemfile.lock, *.gemspec | gem, bundler |   
   | 17          | Rust        | Build, Buildless   | Cargo.toml, Cargo.lock | cargo |   
   | 18          | Scala       | Build, Buildless   | build.sbt, Dependencies.scala  | sbt, plugin: sbt-dependency-graph |   
   | 19          | Swift       | Build, Buildless   | Package.swift, Package.resolved  | swift |  
