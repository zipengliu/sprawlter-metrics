import Vue from 'vue'
import SingleRunView from './SingleRunView.vue'
import ParamAlphaView from './ParamAlphaView.vue'
import BootstrapVue from 'bootstrap-vue'

import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'

Vue.config.productionTip = false;
Vue.use(BootstrapVue);

const routes = {
  'parameter-analysis': ParamAlphaView,
  'single-run': SingleRunView,
};

let paths = window.location.pathname.split('/');
let which_route = paths[1];
console.assert(which_route in routes);

new Vue({
  render: h => h(routes[which_route]),
}).$mount('#app');
