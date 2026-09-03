WHR="examples/spe11b"
OUT="test_outputs/docs_tutorial"
. tests/scripts/initialize_output_folders.sh $OUT
. tests/scripts/get_plopm.sh
mkdir $OUT
cp $WHR.toml $OUT/my_spe11b.toml
pyopmspe11 -i $OUT/my_spe11b.toml -o $OUT/my_spe11b -m deck
pyopmspe11 -i $OUT/my_spe11b.toml -o $OUT/my_spe11b -m flow
pyopmspe11 -i $OUT/my_spe11b.toml -o $OUT/my_spe11b -m data -g all -t 5 -r 50,1,15 -w 1
pyopmspe11 -i $OUT/my_spe11b.toml -o $OUT/my_spe11b -m plot -g all -t 5 -r 50,1,15 -w 1
plopm -i $OUT/my_spe11b/flow/MY_SPE11B -o $OUT -v co2m -cbn 3 -cbf .1e -t 'CO$_2$ mass at the end of the simulation' -mv satnum -mt 1e4 -cbl 'kg' -c RdBu_r -yu km -xu km -xf .1f -yf .1f -fs 10,8 -fz 16
