# Use an official Python image
FROM python:3.9

# Install system dependencies
# For tables, building native extensions, Shapely, GDAL, CMake, PyAudio, PyGraphviz, and PyGObject
RUN apt-get update && apt-get install -y \
    libhdf5-serial-dev \
    build-essential \
    libgeos-dev \
    gdal-bin \
    python3-gdal \
    cmake \
    portaudio19-dev \
    graphviz \
    libgraphviz-dev \
    libgirepository1.0-dev \
    gir1.2-glib-2.0 \
    libcairo2-dev

# Optionally, upgrade pip to the latest version
RUN pip install --upgrade pip

# Explicitly install Cython and NumPy
RUN pip install Cython numpy

# Set the working directory
WORKDIR /usr/src/app

# Copy the current directory contents into the container
COPY requirements.txt ./

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Your additional commands here
