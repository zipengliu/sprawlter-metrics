if [[ $# -eq 0 ]] ; then
    echo 'specify output dir name'
    exit 1
fi

results_dir=../results-demo/public/data/$1
src_dir=../../data/ALL-3

if [ ! -d $results_dir ]; then
    mkdir $results_dir
fi

echo $results_dir
find $src_dir -name *_result.json
find $src_dir -name *_result.json -exec mv {} $results_dir/ \;
