<template>
  <div id="app">
    <ComparisonView :results="results" :dataPath="dataPath" />
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
        data: () => ({results: [], dataPath: null}),
        mounted() {
            let dataPath = `/data${window.location.pathname}`;
            axios.get(`${dataPath}/graphs.txt`).then(response => {
                let graphNames = response.data.split('\n').map(l => l.trim()).filter(l => l.length > 0);
                console.log(graphNames);
                Promise.all(graphNames.map(n => axios.get(`${dataPath}/${n}_result.json`)))
                    .then(responses => {
                        this.results = responses.map(r => r.data);
                        this.dataPath = dataPath;
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
    margin-top: 60px;
  }
</style>
