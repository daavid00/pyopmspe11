WHR="examples/spe11b"
OUT="test_outputs/docs_via_deck_hello_world"
. tests/scripts/initialize_output_folders.sh $OUT
. tests/scripts/get_plopm.sh
pyopmspe11 -i $WHR.toml -o $OUT/spe11b -m all -g all -t 5 -r 50,1,15 -w 1
cp $OUT/spe11b/figures/spe11b_tco2_2Dmaps.png $OUT
for f in immiscible isothermal convective; do
    cp $WHR.toml $OUT/$f.toml
    sed -i.bak "s/complete/$f/g" $OUT/$f.toml && rm -f $OUT/$f.toml.bak
    pyopmspe11 -i $OUT/$f.toml -o $OUT/$f -m all -g all -t 5 -r 50,1,15 -w 1 &
done
wait
cd $OUT
pyopmspe11 -c spe11b
cd ../..
plopm -i $OUT/isothermal/flow/ISOTHERMAL -v sgas -t 'Isothermal simulation (end of simulation)' -o $OUT
plopm -i "$OUT/immiscible/data/spe11b_time_series $OUT/convective/data/spe11b_time_series" -o $OUT -cc 1,4 -llb "Immiscible  Convective" -tu y -yl 'mobA [kg]' -xf .0f -x '[0,25]' -xnt 6 -fz 20 -fs 10,5 -yf .1e -ls 'solid,solid' -lw 4 -sp 1
