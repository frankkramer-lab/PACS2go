# PACS2go 2.0 

This *Picture Archiving and Communication System* is designed and implemented to support researchers manage medical images and metadata.

Version 2.0 replaces Orthanc with the open-source imaging informatics software platform XNAT (https://www.xnat.org/).

The PACS2go 2.0 user interface can currently be accessed via http://vm204-misit.informatik.uni-augsburg.de:5000/ using the Uni Augsburg VPN.


## Getting Started

This project requires an installation of Docker (see: https://docs.docker.com/engine/install/)

```bash
# Clone this repository
$ git clone https://git.rz.uni-augsburg.de/misit-bachelor/pacs2go.git

# Go into the repository
$ cd pacs2go

# Start services via docker-compose
$ docker-compose up
```

## Built with 

- Docker (20.10.18) with docker-compose (1.29.2)
- pyxnat (1.4)
- dash (2.6.1)
- dash-uploader (0.6.0)

