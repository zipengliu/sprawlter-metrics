<template>
  <div>
    <h3>Full results <span v-if="graphNames">(#layouts: {{ graphNames.length }})</span></h3>
    <!--<h3 v-if="runid">-->
      <!--{{ runid }}-->
    <!--</h3>-->
    <div class="timestamp" v-if="timestamp">
    Time: {{ timestamp.toString() }}
    </div>
    <!--<div class="parameters" v-if="parameters">-->
      <!--Parameters: {{ JSON.stringify(parameters) }}-->
    <!--</div>-->
    <div class="legends">
      Legends: A for area-aware metric, S for sprawl ratio, C for count,  A/C is the average penalty.  A and C are broken down by metanode + leafnode.
    </div>

    <ComparisonTable :results="results" :parameters="parameters" />

  </div>
</template>

<script>
  import axios from 'axios'
  import ComparisonTable from '~/components/ComparisonTable.vue'

  // Server side URL must be provided to axios
  let baseURL = 'http://localhost:3000';

  export default {

    asyncData({ params }) {
      console.log(params);

      return axios.get(`${baseURL}/graphs.txt`).then(response => {
        let graphNames = response.data.split('\n').map(l => l.trim()).filter(l => l.length > 0);
        console.log(graphNames);
        return Promise.all(graphNames.map(n => axios.get(`${baseURL}/data/${params.run}/${n}_result.json`))).then(responses => {
          let res = responses.map(r => r.data).map((x, i) => ({...x, name: graphNames[i]}));
          return {
            results: res,
            runid: params.run,
            timestamp: new Date(res[res.length - 1].end_time * 1000),
            parameters: res[0].parameters,
            graphNames
          }
        })
      })
    },

    components: {
      ComparisonTable
    }
  }
</script>

<style scoped>
  h3 {
    text-align: center;
  }
   .timestamp, .parameters, .legends{
    text-align: left;
    font-size: 14px;
  }
  .parameters {
  }
  .legends {
    margin-bottom: 20px;
    font-weight: bold;
  }
</style>
