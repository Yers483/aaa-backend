#!/bin/bash
docker run -v $PWD:/app -p 8080:8080 plate_reader:0.0.6
