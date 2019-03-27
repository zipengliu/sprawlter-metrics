#!/usr/bin/env bash

run_alpha()
{
    results_dir=../results-demo/public/data
    output_dir=$results_dir/count-only-$1
    mkdir -p $output_dir
    python run-all.py --data_dir=../../data/ALL --output_dir=$output_dir \
        --skip_AS_metrics --ee=quadratic \
        --alpha_nn=0.1 --alpha_ne=0.1 --alpha_ee=0.1 > ./logs/count-only-$1.log

}
export -f run_alpha

#    The final run using the chosen parameter
run_chosen()
{
    results_dir=../results-demo/public/data
    output_dir=$results_dir/final-$1
    mkdir -p $output_dir
    python run-all.py --data_dir=../../data/ALL --output_dir=$output_dir \
        --ee=quadratic --alpha_nn=0.2 --alpha_ne=0.2 --alpha_ee=0.2 > ./logs/final-$1.log
}
export -f run_chosen


#parallel --jobs 2 run_alpha ::: 1 2 3 4 5
parallel --jobs 4 run_chosen ::: 1 2 3 4

#run_chosen
