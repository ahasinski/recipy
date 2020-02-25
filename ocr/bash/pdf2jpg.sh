#!/bin/bash
f=$0;
sips -s format jpeg -s formatOptions 100 "${f}" --out "../jpgs/${f%pdf}jpg";