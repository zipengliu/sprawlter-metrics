<template>
    <div id="app">
        <h3 v-if="dataPath">
           {{ dataPath.replace('/data/', '') }}
        </h3>
        <div class="timestamp" v-if="timestamp">
            Time: {{ timestamp.toString() }}
        </div>
        <div class="parameters" v-if="parameters">
            Parameters: {{ JSON.stringify(parameters) }}
        </div>
        <div class="legends">
            Legends: P for penalty, S for sprawl ratio, normP for normalized penalty, C for count.  P and C are broken down by metanode + leafnode.
        </div>
        <ComparisonView :results="results" :dataPath="dataPath" :parameters="parameters" />
    </div>
</template>

<script>
    import ComparisonView from './components/ComparisonView.vue';
    import axios from 'axios';

    export default {
        name: 'app',
        components: {
            ComparisonView
        },
        data: () => ({results: [], dataPath: null, timestamp: null, parameters: null}),
        mounted() {
            let dataPath = `/data${window.location.pathname}`;
            axios.get(`${dataPath}/graphs.txt`).then(response => {
                let graphNames = response.data.split('\n').map(l => l.trim()).filter(l => l.length > 0);
                console.log(graphNames);
                Promise.all(graphNames.map(n => axios.get(`${dataPath}/${n}_result.json`)))
                    .then(responses => {
                        this.results = responses.map(r => r.data);
                        this.dataPath = dataPath;
                        this.timestamp = new Date(this.results[this.results.length - 1].end_time * 1000);
                        this.parameters = this.results[0].parameters;
                        this.graphNames = graphNames;
                    })
            })
        }

    }
</script>

<style>
    #app {
        font-family: 'Avenir', Helvetica, Arial, sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        text-align: center;
        color: #2c3e50;
        margin-top: 20px;
    }
    .timestamp, .parameters, .legends{
        text-align: left;
        font-size: 14px;
    }
    .parameters {
    }
    .legends {
        margin-bottom: 20px;
    }
</style>
