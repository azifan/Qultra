FROM ubuntu:20.04

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && \
    apt-get -y install gcc mono-mcs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/philipsRfParser

COPY philips_rf_parser.c philips_rf_parser.c

RUN gcc -c philips_rf_parser.c
RUN gcc -o philips_rf_parser philips_rf_parser.o
RUN mkdir /shared

# CMD ["./philips_rf_parser", "data.rf", "161611776", "920", "partA"]
# /Users/davidspector/Downloads/C3P11SED00_20180821_102323.rf

