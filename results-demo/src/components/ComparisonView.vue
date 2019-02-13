<template>
    <div>
        <b-table hover :items="items" :fields="fields">
            <template slot="name" slot-scope="data">
                <div class="graph-property">{{ data.item.name }}</div>
                <div class="graph-property">
                    &num;leaf-nodes = {{ data.item.numberOfNodes }} <br/>
                    &num;meta-nodes = {{ data.item.numberOfMetanodes }} <br/>
                    &num;edges = {{ data.item.numberOfEdges }} <br/>
                    &num;levels = {{ data.item.numberOfLevels }}
                </div>
            </template>
            <template slot="image" slot-scope="data">
                <img class="graph-image" v-bind:src="data.item.imagePath" alt="">
            </template>
            <template slot="nn" slot-scope="data">
                <div class="metrics">
                    <div>{{ fixedPrecision(data.item.nnPenalty) }}</div>
                    <div>{{ data.item.nnCount }}</div>
                </div>
            </template>
            <template slot="ne" slot-scope="data">
                <div class="metrics">
                    <div>{{ fixedPrecision(data.item.nePenalty) }}</div>
                    <div>{{ data.item.neCount }}</div>
                </div>
            </template>
            <template slot="ee" slot-scope="data">
                <div class="metrics">
                    <div>{{ fixedPrecision(data.item.eePenalty) }}</div>
                    <div>{{ data.item.eeCount }}</div>
                </div>
            </template>
            <template slot="executionTime" slot-scope="data">
                {{ fixedPrecision(data.item.nnTime, 0) }} +
                {{ fixedPrecision(data.item.neTime, 0) }} +
                {{ fixedPrecision(data.item.eeTime, 0) }} =
                {{ fixedPrecision(data.item.totTime, 0) }}
            </template>
        </b-table>
    </div>
</template>

<script>
    export default {
        name: 'ComparisonView',
        props: ['results', 'dataPath'],
        data: () => ({
            fields: [
                {key: 'name', label: 'Graph'},
                {key: 'image', label: 'Image'},
                // {key: 'numberOfNodes', label: '#Nodes'},
                // {key: 'numberOfEdges', label: '#Edges'},
                // {key: 'graph-property', label: '#Nodes</br>#Edge'}       // TODO
                {key: 'nn', label: 'Node-node (penalty, count)'},
                {key: 'ne', label: 'Node-edge (penalty, count)'},
                {key: 'ee', label: 'Edge-edge (penalty, count)'},
                {key: 'area', label: 'Area (min bbox)', formatter: 'fixedPrecision'},
                // {key: 'nnPenalty', label: 'Node-node Penalty', formatter: 'fixedPrecision'},
                // {key: 'nnCount', label: 'Node-node Count'},
                // {key: 'nePenalty', label: 'Node-edge Penalty', formatter: 'fixedPrecision'},
                // {key: 'neCount', label: 'Node-edge Count'},
                // {key: 'eePenalty', label: 'Edge-edge Penalty', formatter: 'fixedPrecision'},
                // {key: 'eeCount', label: 'Edge-edge Count'},
                {key: 'executionTime', label: 'Execution Time (s) (NN+NE+EE=ALL)'},
                ]
        }),
        computed: {
            items: function() {
                return this.results.map(r => ({
                    name: r.tlpFile.replace('.tlp', ''),
                    numberOfNodes: r.graph.numberOfNodes,
                    numberOfEdges: r.graph.numberOfEdges,
                    numberOfLevels: r.graph.numberOfLevels,
                    numberOfMetanodes: r.graph.numberOfMetaNodes,
                    imagePath: `/images/${r.tlpFile.replace('.tlp', '.png')}`,
                    nnPenalty: r.metrics.nn.total_penalty,
                    nnCount: r.metrics.nn.total_count,
                    nePenalty: r.metrics.ne.total_penalty,
                    neCount: r.metrics.ne.total_count,
                    eePenalty: r.metrics.ee.total_penalty,
                    eeCount: r.metrics.ee.total_count,
                    area: computeRectArea(r.metrics.area),
                    nnTime: r.metrics.nn.execution_time,
                    neTime: r.metrics.ne.execution_time,
                    eeTime: r.metrics.ee.execution_time,
                    totTime: r.metrics.nn.execution_time + r.metrics.ne.execution_time + r.metrics.ee.execution_time,
                }));
            }
        },
        methods: {
            fixedPrecision: (v, p=2) => v.toFixed(p),
        }
    }

    function computeRectArea(a) {
        return (a[1][0] - a[0][0]) * (a[1][1] - a[0][1]);
    }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
    img.graph-image {
        max-width: 300px;
        max-height: 300px;
    }
    .graph-property {
        text-align: left;
    }
    .metrics {
        text-align: left;
    }
</style>
