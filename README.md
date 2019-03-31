Steps of computational pipeline for SA metrics
=====

1. Convert graph format (Python).  We convert a variety of input graph formats into Tulip format, as Tulip provides several useful layout algorithms.
2. Apply the four layout algorithms. Two are run within the version 5.2.1 of Tulip (GEM and FM3); we use the 2008 version of GrouseFlocks, and a version of Koala modified to save in Tulip format. The output in all four cases is the geometric information of nodes and edges (position, area, shape, length) in Tulip format.
3. Extract geometries and node hierarchy (Python).  We then parse the 52 layouts in Tulip format, extract the information of geometry and node hierarchy, and store it in JSON format.
4. Compute metrics (Python).  We implement the SA metrics for the NN, NE, and EE families and also their respective count-based metrics, and also the global readability metrics of node-node overlap and crossing angle of Dunne et al. We use the Shapely Python package for manipulation of geometry.
5. Display and analyze results for comparison.  We display the computed metrics of each layout in a table with HTML and JavaScript, and we write Python scripts to analyze parameters and computational time.


Folder `comparative-analysis`
=====

* `param-*`: runs for parameter analysis.  The metric family (either NN, NE or EE), the minimum penalty fraction (alpha), and the penalty function curve shape (gamma) is indicated in the folder name.
* `count-only`: only compute counts to compare computational time between SA and count-based approach
* `all-metrics`: the run with chosen parameter (alpha=0.2 for NN, NE, and EE)


Folder `scripts`
=====

* `sa_metrics.py`: main script to compute the SA metrics and also the count-based metrics.
* `geometric.py`: geometric functions used by SA metrics
* `graph-format-conversion/*.{py|ipynb}`: script in Python or Python notebook to convert various graph formats to Tulip, and then to a JSON format that can be read by the main script.
* `analysis/*.ipynb`: scripts to analyze computational time, parameters, and plot penalty mapping functions.


Folder `full-results-table`
=====

* `full-results.html`: the table of all metrics of all 52 layouts
* `images/`: the layout pictures
* `full-results.png`: the screenshot of the html file above


Folder `layouts`
=====
The layout information in JSON format (after step 3 in the computational pipeline) 
