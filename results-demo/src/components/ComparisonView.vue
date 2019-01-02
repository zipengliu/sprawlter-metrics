<template>
    <div>
        <b-table hover :items="items" :fields="fields">
            <template slot="image" slot-scope="data">
                <img class="graph-image" v-bind:src="data.item.imagePath" alt="">
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
                {key: 'numberOfNodes', label: '#Nodes'},
                {key: 'numberOfEdges', label: '#Edges'},
                {key: 'nnPenalty', label: 'Node-node Penalty', formatter: 'fixedPrecision'},
                {key: 'nnCount', label: 'Node-node Count'},
                {key: 'nePenalty', label: 'Node-edge Penalty', formatter: 'fixedPrecision'},
                {key: 'neCount', label: 'Node-edge Count'},
                {key: 'eePenalty', label: 'Edge-edge Penalty', formatter: 'fixedPrecision'},
                {key: 'eeCount', label: 'Edge-edge Count'},
                {key: 'executionTime', label: 'Execution Time (s)', formatter: 'fixedPrecision'},
                ]
        }),
        computed: {
            items: function() {
                return this.results.map(r => ({
                    name: r.tlpFile.replace('.tlp', ''),
                    numberOfNodes: r.graph.numberOfNodes,
                    numberOfEdges: r.graph.numberOfEdges,
                    imagePath: `${this.dataPath}/${r.tlpFile.replace('.tlp', '.png')}`,
                    nnPenalty: r.metrics.nn.total_penalty,
                    nnCount: r.metrics.nn.total_count,
                    nePenalty: r.metrics.ne.total_penalty,
                    neCount: r.metrics.ne.total_count,
                    eePenalty: r.metrics.ee.total_penalty,
                    eeCount: r.metrics.ee.total_count,
                    executionTime: r.metrics.nn.execution_time + r.metrics.ne.execution_time + r.metrics.ee.execution_time,
                }));
            }
        },
        methods: {
            fixedPrecision: (v) => v.toFixed(2),
        }
    }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
    img.graph-image {
        max-width: 300px;
        max-height: 300px;
    }
</style>
