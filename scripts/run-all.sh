#!/usr/bin/env bash

run_alpha_nn()
{
    results_dir=../comparative-analysis/static/data
    output_dir=$results_dir/param-nn-ne-$1
    mkdir -p $output_dir
    python run-all.py --data_dir=../../data/ALL --output_dir=$output_dir \
        --skip_Dunne_metrics \
        --skip_ee_computation \
        --ee=quadratic  \
        --alpha_nn=$1 --alpha_ne=$1 --alpha_ee=$1 > ./logs/param-nn-ne-$1.log

}
export -f run_alpha_nn

run_alpha_ee()
{
    results_dir=../comparative-analysis/static/data
    output_dir=$results_dir/param-ee-quadratic-$1
    mkdir -p $output_dir
    python run-all.py --data_dir=../../data/ALL --output_dir=$output_dir \
        --skip_Dunne_metrics \
        --skip_nn_computation --skip_ne_computation \
        --ee=quadratic  \
        --alpha_nn=$1 --alpha_ne=$1 --alpha_ee=$1 > ./logs/param-ee-quadratic-$1.log

}
export -f run_alpha_ee

#  The final run using the chosen parameter
run_all_metrics()
{
    results_dir=../comparative-analysis/static/data
    output_dir=$results_dir/all-metrics-$1
    mkdir -p $output_dir
    python run-all.py --data_dir=../../data/ALL --output_dir=$output_dir \
        --ee=quadratic --alpha_nn=0.2 --alpha_ne=0.2 --alpha_ee=0.2 > ./logs/all-metrics-$1.log
}
export -f run_all_metrics


#parallel --jobs 3 run_alpha_nn ::: 0.01 0.2 0.4 0.6 0.8 0.99
#parallel --jobs 2 run_alpha_ee ::: 0.01 0.07 0.13 0.20 0.26 0.328

parallel --jobs 4 run_all_metrics ::: 1

