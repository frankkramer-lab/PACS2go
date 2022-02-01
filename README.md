# PACS2go - Conception and Development of a Picture Archiving and Communication System for Research

## Table of Contents

- [General information](#general-info)
- [Built with](#built-with)
- [Features](#features)
- [Getting Started](#getting-started)
- [Status / Future Work](#status)



## General Info

This *Picture Archiving and Communication System* was designed and implemented in order to help researchers and medical staff manage medical images in a research context. After a quick and easy setup, the system is able to store DICOM images in an ORTHANC instance and lets the user examine them via the included OHIF viewer. Additional tools enable the user to convert non-DICOM imaging files &mdash; such as JPEG or NIfTI &mdash; to DICOM format and also make it possible to pseudonymize DICOM files. All of which can also be done through an intuitive web interface.

To view the web service from which all resources can be navigated to, connect to the Universität Augsburg VPN and visit http://vm204-misit.informatik.uni-augsburg.de/web  



## Built with 

- Docker (20.10.12) with docker-compose (1.29.2)
- ohif/viewer (v4.9.8)
- orthanc-plugins (1.9.7)
- Python (3.6.9)
- Flask (2.0.2)
- gunicorn (20.1.0)
- pydicom (2.2.2)
- Pillow (5.1.0)
- nibabel (3.2.1)
- pyorthanc (0.2.14)



## Features

- Pseudonymisation
  - removes the identity from a DICOM file and replaces it with a pseudonym
  - the pseudonym mapping is written to a .csv file whose destination can be chosen by the user
- DICOM converter
  - converts different imaging formats to DICOM format
  - handle: 
    - a single file or a directory of multiple files
    - .jpeg, .png, .bmp, .nii(.gz)
- an ORTHANC DICOM server instance 
- an OHIF viewer
  - connected to ORTHANC's DICOMweb service &rarr; all images saved to ORTHANC can be viewed here
- web service / web interface
  - navigation to all services
  - web interface for Pseudonymisation and DICOM converter with integrated upload function



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

The services should now run on your localhost at: http://localhost:80/ 

More precisely:

- web service: http://localhost:80/web
- OHIF: http://localhost:80/
- ORTHANC: http://localhost:80/pacs-admin 



## Status / Future Work

- nginx addresses:
  - web-service should be http://localhost:80/ and OHIF should be http://localhost:80/ohif (makes more sense for navigation)
  - due to a problem described in a comment on issue #15, this is currently not possible
- DICOM converter
  - currently the converter only converts .png, .bmp, .jgp and .nii(.gz) files
  - other common medical imaging formats (especially in pathology) are TIFF and SVS &rarr; implement .tiff and .svs handling
- Security
  - idea 1: Web Service Login Interface
    - currently uploads via the Pseudonymisation and Converter tools don't require a password &rarr; create a login interface for the entire web service
  - idea 2: Keycloak
    - use keycloak as described here: https://docs.ohif.org/deployment/recipes/user-account-control.html