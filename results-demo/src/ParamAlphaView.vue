<template>
    <div id="app">
        <h3>Parameter analysis for alpha</h3>

        <ProgressionTable :data="data" :alphaValues="alphaValues" :graphNames="graphNames" />
    </div>
</template>

<script>
    import ProgressionTable from './components/ProgressionTable.vue';
    import axios from 'axios';

    let alphaValues = ['0.01', '0.1', '0.2', '0.5', '0.8', '0.99'];
    let graphNamesNNNE = ['touch-leaf', 'touch-meta', 'some-leaf', 'some-leaf', 'near-max-leaf', 'near-max-meta'];
    let graphNamesEE = ['ortho', 'half', 'near-glancing'];
    let paths = window.location.pathname.split('/');
    let which_case = paths[2];
    let eeFuncType = which_case === 'ee'? paths[3]: 'linear';

    export default {
        name: "ParamAlphaView",
        components: {
            ProgressionTable,
        },
        data: () => ({
            graphNames: (which_case === 'ee'? graphNamesEE: graphNamesNNNE).map(x => `progression-${which_case}-${x}`),
            folderNames: alphaValues.map(a => `param-${eeFuncType}-${a}`),
            data: {},
        }),
        mounted() {
            console.log(this.graphNames);
            console.log(this.folderNames);

            let promises = [];
            for (let f of this.folderNames) {
                this.data[f] = {};
                for (let g of this.graphNames) {
                    promises.push(axios.get(`/data/${f}/${g}_result.json`).then(r => {
                        this.data[f][g] = r.data;
                    }))
                }
            }

            Promise.all(promises).then(() => {
                console.log('All data fetched!');
                console.log(this.data);
            })
        }
    }
</script>

<style scoped>

</style>