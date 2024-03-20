FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive
RUN mkdir -p /home/downloads

## install initial packages
RUN apt-get update && apt-get install -y vim unzip git wget curl software-properties-common apt-transport-https gnupg -yqq dos2unix

## install python & runtime requirements
RUN apt-get install -y python3.8 python3-pip
COPY requirements.txt /opt/requirements.txt
RUN pip install -r /opt/requirements.txt

## install compile requirements
## install java jdk
COPY jdk-11.0.1_linux-x64_bin.tar.gz /home/downloads/jdk-11.0.1_linux-x64_bin.tar.gz
RUN tar -xzvf /home/downloads/jdk-11.0.1_linux-x64_bin.tar.gz -C /opt
ENV JAVA_HOME=/opt/jdk-11.0.1
ENV CLASSPATH=.:$JAVA_HOME/lib
ENV PATH=$JAVA_HOME/bin:$PATH
## install maven
COPY apache-maven-3.8.6-bin.tar.gz /home/downloads/apache-maven-3.8.6-bin.tar.gz
RUN tar -xzvf /home/downloads/apache-maven-3.8.6-bin.tar.gz -C /opt
ENV MAVEN_HOME=/opt/apache-maven-3.8.6
ENV PATH=$MAVEN_HOME/bin:$PATH
## install gradle
COPY gradle-6.8.2-bin.zip /home/downloads/gradle-6.8.2-bin.zip
RUN unzip -d /opt /home/downloads/gradle-6.8.2-bin.zip
ENV GRADLE_HOME=/opt/gradle-6.8.2
ENV PATH=$GRADLE_HOME/bin:$PATH
## install leiningen
COPY lein /usr/bin
RUN chmod a+x /usr/bin/lein
WORKDIR /usr/bin
RUN lein
WORKDIR /
## install Scala sbt
RUN echo "deb https://repo.scala-sbt.org/scalasbt/debian all main" | tee /etc/apt/sources.list.d/sbt.list
RUN echo "deb https://repo.scala-sbt.org/scalasbt/debian /" | tee /etc/apt/sources.list.d/sbt_old.list
RUN curl -sL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x2EE0EA64E40A89B84B2DF73499E82A75642AC823" | gpg --no-default-keyring --keyring gnupg-ring:/etc/apt/trusted.gpg.d/scalasbt-release.gpg --import
RUN chmod 644 /etc/apt/trusted.gpg.d/scalasbt-release.gpg
RUN apt-get update && apt-get install -y sbt
RUN mkdir -p /root/.sbt/1.0/plugins
COPY plugins.sbt /root/.sbt/1.0/plugins/plugins.sbt
## install nodejs, npm
RUN curl -fsSL https://deb.nodesource.com/setup_17.x | bash -
RUN apt-get install -y nodejs
## install go
RUN add-apt-repository ppa:longsleep/golang-backports
RUN apt-get update && apt-get install -y golang-go
RUN go env -w GOPROXY=https://goproxy.cn,direct
## install php, composer
RUN apt-get install -y php-common libapache2-mod-php php-cli
COPY composer_install.sh /home/downloads/composer_install.sh
RUN /bin/bash /home/downloads/composer_install.sh
RUN mv composer.phar /usr/bin/composer
RUN composer config -g repo.packagist composer https://mirrors.aliyun.com/composer/
## install cargo
RUN apt-get install -y cargo
RUN mkdir -p /root/.cargo
COPY config /root/.cargo/config
## install cpanm
RUN wget http://xrl.us/cpanm -O /usr/bin/cpanm
RUN chmod +x /usr/bin/cpanm
## install gem, bundler
RUN apt-get install -y ruby-full
RUN gem install bundler
## install dart(flutter)
COPY flutter_linux_3.0.5-stable.tar.xz /home/downloads/flutter_linux_3.0.5-stable.tar.xz
RUN tar -xvf /home/downloads/flutter_linux_3.0.5-stable.tar.xz -C /opt
ENV PATH=/opt/flutter/bin:$PATH
ENV FLUTTER_STORAGE_BASE_URL="https://mirrors.tuna.tsinghua.edu.cn/flutter"
ENV PUB_HOSTED_URL="https://mirrors.tuna.tsinghua.edu.cn/dart-pub"
RUN git config --global --add safe.directory /opt/flutter
RUN rm /opt/flutter/bin/cache/lockfile
## install swift
COPY swift-5.7-RELEASE-ubuntu20.04.tar.gz /home/downloads/swift-5.7-RELEASE-ubuntu20.04.tar.gz
RUN tar -xzvf /home/downloads/swift-5.7-RELEASE-ubuntu20.04.tar.gz -C /opt
ENV PATH=/opt/swift-5.7-RELEASE-ubuntu20.04/usr/bin:$PATH
## install erlang, rebar3
RUN wget -O- https://packages.erlang-solutions.com/ubuntu/erlang_solutions.asc | apt-key add -
RUN echo "deb https://packages.erlang-solutions.com/ubuntu focal contrib" | tee /etc/apt/sources.list.d/erlang.list
RUN apt-get update && apt-get install -y erlang
COPY rebar3 /opt/rebar3
WORKDIR /opt/rebar3
RUN ./bootstrap
RUN ./rebar3 local install
ENV PATH=/root/.cache/rebar3/bin:$PATH
WORKDIR /
RUN mkdir -p /root/.config/rebar3
COPY rebar.config /root/.config/rebar3/rebar.config
## install elixir, mix
RUN apt-get install -y elixir
RUN mkdir -p /root/.mix/archives
COPY hex-1.0.1 /root/.mix/archives/hex-1.0.1
RUN mix hex.config mirror_url https://hexpm.upyun.com
RUN mix local.rebar rebar3 /root/.cache/rebar3/bin/rebar3
## install haskell-stack
COPY stack /usr/bin
RUN mkdir -p /root/.stack
COPY config.yaml /root/.stack/config.yaml

RUN rm -r /home/downloads
CMD ["/bin/bash"]
