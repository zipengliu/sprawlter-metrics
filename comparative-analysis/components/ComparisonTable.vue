<template>
    <div class="comparison-table">
        <b-table bordered :items="items" :fields="fields">
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
          <template slot="sprawl" slot-scope="data">
            <div class="metrics">
              <div>S={{ fixedPrecision(data.item.metrics.sprawl) }}</div>
              <div>b-box area={{ fixedPrecision(data.item.area) }}</div>
            </div>
          </template>
          <template slot="nn" slot-scope="data">
                <div class="metrics">
                    <div class="highlight">A={{ penalty_levels_repr(breakdown_by_level(data.item.metrics.nn.penalty_by_level)) }}={{ fixedPrecision(data.item.nnPenalty) }}</div>
                    <div>Sprawlter={{ fixedPrecision(data.item.metrics.nn.sc) }}</div>

                    <div class="count highlight">C={{ count_levels_repr(breakdown_by_level(data.item.metrics.nn.count_by_level)) }}={{ data.item.nnCount }}</div>
                    <div>A/C={{ pc_ratio(data.item.metrics, 'nn') }}</div>
                    <!--<div>SA/C={{ norm_pc_ratio(data.item.metrics, 'nn') }}</div>-->

                    <div v-if="data.item.metrics.nn.hasOwnProperty('dunne_ratio')" class="dunne">
                        Dunne's ratio={{ fixedPrecision(data.item.metrics.nn.dunne_ratio, 2, true) }}
                    </div>
                </div>
            </template>
            <template slot="ne" slot-scope="data">
                <div class="metrics">
                    <div class="highlight">A={{ penalty_levels_repr(breakdown_by_level(data.item.metrics.ne.penalty_by_level)) }}={{ fixedPrecision(data.item.nePenalty) }}</div>
                    <div>Sprawlter={{ fixedPrecision(data.item.metrics.ne.sc) }}</div>

                    <div class="count highlight">C={{ count_levels_repr(breakdown_by_level(data.item.metrics.ne.count_by_level)) }}={{ data.item.neCount }}</div>
                    <div>A/C={{ pc_ratio(data.item.metrics, 'ne') }}</div>
                    <!--<div>SA/C={{ norm_pc_ratio(data.item.metrics, 'ne') }}</div>-->
                </div>
            </template>
            <template slot="ee" slot-scope="data">
                <div class="metrics">
                    <div class="highlight">A={{ fixedPrecision(data.item.eePenalty) }}</div>
                  <div>Sprawlter={{ fixedPrecision(data.item.metrics.ee.sc) }}</div>

                  <div class="count highlight">C={{ data.item.eeCount }}</div>

                    <div>A/C={{ pc_ratio(data.item.metrics, 'ee') }}</div>
                    <!--<div>SA/C={{ norm_pc_ratio(data.item.metrics, 'ee') }}</div>-->
                    <div v-if="data.item.avrAngle !== 'NA'">avg. angle={{ data.item.avrAngle }}</div>

                    <div v-if="data.item.metrics.ee.hasOwnProperty('dunne_ratio')" class="dunne">
                        Dunne's ratio={{ fixedPrecision(data.item.metrics.ee.dunne_ratio, 2, true) }}
                    </div>
                </div>
            </template>
            <template slot="executionTime" slot-scope="data">
                {{ fixedPrecision(data.item.nnTime, 0, false) }} +
                {{ fixedPrecision(data.item.neTime, 0, false) }} +
                {{ fixedPrecision(data.item.eeTime, 0, false) }} =
                {{ fixedPrecision(data.item.totTime, 0, false) }}
            </template>
        </b-table>
    </div>
</template>

<script>
    import numeral from 'numeral';

    export default {
        name: 'ComparisonTable',
        props: ['results', 'parameters'],
        data: () => ({
            fields: [
                {key: 'name', label: 'Graph'},
                {key: 'image', label: 'Image'},
                {key: 'sprawl', label: 'Sprawl'},
                {key: 'nn', label: 'Node-node'},
                {key: 'ne', label: 'Node-edge'},
                {key: 'ee', label: 'Edge-edge'},
                // {key: 'executionTime', label: 'Execution Time (s) (NN+NE+EE=ALL)'},
                ]
        }),
        computed: {
            items: function() {
                console.log(this.parameters);
                  console.log(this.results[0].name);
                return this.results.map(r => ({
                    name: r.name,
                    numberOfNodes: r.graph.numberOfNodes,
                    numberOfEdges: r.graph.numberOfEdges,
                    numberOfLevels: r.graph.numberOfLevels,
                    numberOfMetanodes: r.graph.numberOfMetaNodes,
                    imagePath: `images/${r.name}.png`,
                    metrics: r.metrics,
                    nnPenalty: r.metrics.nn.total_penalty,
                    nnCount: r.metrics.nn.total_count,
                    nePenalty: r.metrics.ne.total_penalty,
                    neCount: r.metrics.ne.total_count,
                    eePenalty: r.metrics.ee.total_penalty,
                    eeCount: r.metrics.ee.total_count,
                    area: r.graph.totalArea,
                    nnTime: r.metrics.nn.execution_time,
                    neTime: r.metrics.ne.execution_time,
                    eeTime: r.metrics.ee.execution_time,
                    totTime: r.metrics.nn.execution_time + r.metrics.ne.execution_time + r.metrics.ee.execution_time,
                    avrAngle: r.metrics.ee.total_count == 0? 'NA':
                        numeral(180 / Math.PI * (r.metrics.ee.total_overlap / r.metrics.ee.total_count)).format('0.00')
                }));
            }
        },
        methods: {
            // fixedPrecision: (v, p=0, force=true) => force && v < 10^(-p)? v.toFixed(2): v.toFixed(p),
            fixedPrecision: (v, p=2, force=true) => force && v < 10^(-p)? numeral(v).format('0,0.00'): numeral(v).format('0,0'),
            pc_ratio: (d, which) => d[which].total_count == 0? 'NA':
                numeral(d[which].total_penalty / d[which].total_count, 2).format('0.00'),
            norm_pc_ratio: (d, which) => d[which].total_count == 0? 'NA':
                numeral(d[which].sa / d[which].total_count, 2).format('0.00'),

            // Calculate a breakdown of counts or penalties by metanode and leaf node
            // The row 0 and column 0 are the root level, exclude it because it is always zero
            breakdown_by_level: (t) => {
                let sum = 0;
                for (let i = 0; i < t.length; i++) {
                    for (let j = 0; j < t[i].length; j++) {
                        if (t[i][j] !== 'NA') {
                            sum += t[i][j];
                        }
                    }
                }
                return [sum - t[t.length - 1][t.length - 1], t[t.length - 1][t.length - 1]];
            },
            count_levels_repr: (breakdown) => breakdown.join('+'),
            penalty_levels_repr: (breakdown) => breakdown.map(v => numeral(v).format('0,0.00')).join('+'),


        }
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
        text-align: right;
    }
    .metrics .count {
        margin-top: 10px;
        margin-bottom: 10px;
    }
    .highlight {
        /*font-weight: bold;*/
        /*color: white;*/
        /*background: #000;*/
    }
    .metrics .dunne {
        margin-top: 10px;
    }

    .comparison-table {
      text-align: center;
    }
</style>
