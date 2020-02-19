FROM ubuntu

#ARG github-username=""
#ARG github-password=""

RUN apt update
RUN apt install -y git python3 python3-pip wget curl libpq-dev
RUN pip3 install netaddr pyfiglet tqdm pyasn beautifulsoup4 requests python-daemon slackweb psycopg2

# Install routinator
RUN apt update
RUN apt install -y rsync build-essential
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
RUN /bin/bash -c "source ~/.cargo/env ; cargo install routinator"
RUN /bin/bash -c "source ~/.cargo/env ; routinator init --accept-arin-rpa"
# Set env value
RUN /bin/bash -c "cat  ~/.cargo/env >> ~/.bashrc;"


RUN git clone https://github.com/taiji-k/roamon-alert.git
# roamon-diffをハイフンなしにリネームしてるのは、ハイフンつきだとpythonでimportできないから
RUN cd roamon-alert && git clone https://github.com/taiji-k/roamon-verify.git && mv roamon-verify roamon_verify

# FOR TEST
#RUN git clone https://USERNAME:PASSWORD@github.com/taiji-k/roamon-alert.git --branch  feature-#14_make_docker_env
## roamon-diffをハイフンなしにリネームしてるのは、ハイフンつきだとpythonでimportできないから
#RUN cd roamon-alert && git clone https://USERNAME:PASSWORD@github.com/taiji-k/roamon-diff.git --branch  feature-#17_make_dokcker_env && mv roamon-diff roamon_verify
