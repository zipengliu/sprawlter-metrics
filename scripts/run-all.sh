#!/usr/bin/env bash

run_alpha()
{
    results_dir=../results-demo/public/data
    mkdir -p $results_dir/param-ee-quadratic-$1
    python run-all.py --data_dir=../../data/ALL --output_dir=$results_dir/param-ee-quadratic-$1 \
        --skip_nn_computation --skip_ne_computation --ee=quadratic --alpha_nn=$1 --alpha_ne=$1 --alpha_ee=$1 > ./logs/ee-quadratic-$1.log

}
export -f run_alpha

#    The final run using the chosen parameter
run_chosen()
{
    results_dir=../results-demo/public/data
    output_dir=$results_dir/final-with-dunne-metrics
    mkdir -p $output_dir
    python run-all.py --data_dir=../../data/ALL --output_dir=$output_dir \
        --ee=quadratic --alpha_nn=0.2 --alpha_ne=0.2 --alpha_ee=0.2 > ./logs/final-with-dunne.log
}
export -f run_chosen


#parallel --jobs 2 run_alpha ::: 0.01 0.07 0.13 0.20 0.26 0.328

run_chosen
