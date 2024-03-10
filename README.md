# PACS2go - Towards a Portable Research PACS for Interdisciplinary Collaboration


PACS2go is a portable **Picture Archiving and Communication System** tailored for medical research. It simplifies the storage, sharing, and viewing of medical imaging data, supporting key formats like DICOM and NIfTI. Designed to facilitate interdisciplinary collaboration, PACS2go enables users to work on shared projects, enrich imaging data with metadata, and access it all through an intuitive web interface. 👩‍💻🩻

## Features

- XNAT File Storage: Secure and scalable storage for medical imaging files, supporting various formats including DICOM, NIFTI, and many more.

- PostgreSQL Metadata Store: Efficient organization and retrieval of image metadata, enabling advanced data management.

- Plotly Dash UI: Interactive and user-friendly interface for navigating imaging datasets, visualizing imaging data, accessing metadata, and collaborating with fellow researchers on shared data.

## Architecture

![[docs/Bildschirmfoto 2024-03-10 um 18.05.26.png]]

## Getting Started in Just 3 Steps

To kick off with PACS2go, ensure Docker is installed on your system ([Docker Installation Guide](https://docs.docker.com/engine/install/)).
  

```bash
# 1 - Clone this repository
$ git clone https://git.rz.uni-augsburg.de/misit-bachelor/pacs2go.git

# 2 - Go into the repository
$ cd pacs2go

# 3 - Start services via docker-compose
$ docker-compose up
```
  
🎉  The PACS2go is now live and ready! 🎉 

##### First Steps:
1. Visit port 8888 to set up XNAT and create your first user account.
2. Visit the PACS2go web interface on port 5000, log in and start exploring! 🚀


## User Interface Preview
🛬 Landing page 
![[Capture-2024-03-10-183446.png]]

💽 Upload interface
![[Capture-2024-03-10-183619.png]]

🗂️ Inside a directory
![[Capture-2024-03-10-183701.png]]

🧠 NIfTI viewer
![[Capture-2024-03-10-183822.png]]
  

## Built with

  
- **Docker** (20.10.18) & **docker-compose** (1.29.2): For creating and managing multi-container applications. 🐳
- **Plotly Dash** (2.14.1): Empowers the development of interactive web applications for data visualization. 📈
- **dash-uploader** (0.6.0): Enhances file upload capabilities within Dash applications. 📤
- **Postgres**: A powerful, open-source object-relational database system, used here for efficient metadata storage. 🛢️
- **Dockerized XNAT**: Utilizes the robust XNAT platform within Docker for unparalleled file storage solutions. Check it out [here](https://github.com/NrgXnat/xnat-docker-compose). 🏗️
