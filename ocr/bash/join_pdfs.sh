#!/bin/bash
p_1=$0;
p_2=$1;
p_out=$2;
#echo $p_1 $p_2 $p_out;
#p_2=${p_1%0001.pdf}0002.pdf;
#p_out=../${p_1%-0001.pdf}.pdf;
#"/System/Library/Automator/Combine PDF Pages.action/Contents/Resources/join.py" -o $p_out $p_1 $p_2;
/System/Library/Automator/Combine\ PDF\ Pages.action/Contents/Resources/join.py -o $p_out $p_1 $p_2;
