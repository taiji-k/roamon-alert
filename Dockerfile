FROM ubuntu:18.04
# MAINTAINER name <e-mail@example.com>

ARG username=""
ARG password=""

RUN sed -i.bak -e "s%http://archive.ubuntu.com/ubuntu/%http://ftp.riken.go.jp/Linux/ubuntu/%g" /etc/apt/sources.list

# Suppress some useless errors appear when installaing packages with apt
ENV DEBIAN_FRONTEND noninteractive
ENV DEBCONF_NOWARNINGS yes
ENV TERM linux

# Install packages with apt
ADD ./requirements/apt.txt apt.txt
RUN rm -rf /var/lib/apt/lists/* \
    && apt autoclean \
    && apt update
RUN apt -y --no-install-recommends install software-properties-common \
    && apt-add-repository ppa:deadsnakes/ppa \
    && xargs apt -y --no-install-recommends install < apt.txt \
    && apt clean

# Install routinator
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
RUN /bin/bash -c "source ~/.cargo/env ; cargo install routinator" \
    && /bin/bash -c "source ~/.cargo/env ; routinator init --accept-arin-rpa"

# Set the locale
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8

# Install packages with pip
ADD ./Pipfile Pipfile
ADD ./Pipfile.lock Pipfile.lock
RUN pip3 install --upgrade setuptools \
    && pip3 install pipenv \
    && pipenv install


# RUN git clone https://$username:$password@github.com/taiji-k/roamon-alert.git roamon-alert
RUN git clone https://github.com/taiji-k/roamon-alert.git roamon-alert
WORKDIR /roamon-alert
# Renamed the default clone dir in order to be imported by Python.
# RUN git clone https://$username:$password@github.com/taiji-k/roamon-verify.git roamn_verify
RUN git clone https://github.com/taiji-k/roamon-verify.git roamn_verify

# FOR TEST
#RUN git clone https://USERNAME:PASSWORD@github.com/taiji-k/roamon-alert.git --branch  feature-#14_make_docker_env
## roamon-diffをハイフンなしにリネームしてるのは、ハイフンつきだとpythonでimportできないから
#RUN cd roamon-alert && git clone https://USERNAME:PASSWORD@github.com/taiji-k/roamon-diff.git --branch  feature-#17_make_dokcker_env && mv roamon-diff roamon_verify
