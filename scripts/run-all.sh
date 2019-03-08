#!/usr/bin/env bash

run_alpha()
{
    echo $1
    results_dir=../results-demo/public/data
    mkdir -p $results_dir/param-ee-linear-$1
    python run-all.py --data_dir=../../data/ALL --output_dir=$results_dir/param-ee-linear-$1 \
        --skip_nn_computation --skip_ne_computation --ee=linear --alpha_nn=$1 --alpha_ne=$1 --alpha_ee=$1 > ./logs/ee-linear-$1.log
}
export -f run_alpha

parallel --jobs 2 run_alpha ::: 0.01 0.13 0.26 0.39 0.52 0.637
