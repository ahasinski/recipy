# converts pdf to png
mkdir ../pngs
for f in *.pdf;
  do
    b=$(basename $f .pdf);
    sips -s format png $f --out ../pngs/${b}.png;
  done

mkdir ../jpgs
for f in *.pdf;
  do
    b=$(basename $f .pdf);
    sips -s format jpeg -s formatOptions 100 $f --out ../jpgs/${b}.jpg;
  done

# converts pdf to jpg
mkdir ../jpgs
for i in *.pdf;
  do
    sips -s format jpeg -s formatOptions 100 "${i}" --out "../jpgs/${i%pdf}jpg";
  done

# combine cover and instruct_pdfs into 1 pdf for future reference
for p_1 in *0001.pdf;
  do
    p_2=${p_1%0001.pdf}0002.pdf;
    p_out=../${p_1%-0001.pdf}.pdf;
    "/System/Library/Automator/Combine PDF Pages.action/Contents/Resources/join.py" -o $p_out $p_1 $p_2;
  done

conda activate ocr_01
for img in *0001.png;
  do
    echo $img
    y_out=../ymls/${img%-0001.png}.yml
    python ~/Desktop/code_projects/recipy/ocr/blue_apron_ocr.py -c $img -o manual -w $y_out
  done

for img in *0001.png;
  do
    echo $img;
    y_out=../ymls/${img%-0001.png}.yml;
    echo $y_out;
    python ~/Desktop/code_projects/recipy/ocr/blue_apron_ocr.py -c $img -o auto -w $y_out;
  done