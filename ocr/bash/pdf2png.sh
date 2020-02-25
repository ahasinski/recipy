#!/bin/bash
f_in=$0;
f_out=$1;
sips -s format png $f_in --out $f_out;
#sips -s format png "${f}" --out "../pngs/${f%pdf}png";