import _ from 'lodash';
import { DEVICE_TYPE, OPENCLGA_STATES } from '../shared/constants';
import { ACTION_KEYS } from '../shared/socket';

export const initialState = {
  workers: {}
};

const WORKER_TEMPLATE = {
  'best': null,
  'device': '',
  'ip': '',
  'platform': '',
  'state': OPENCLGA_STATES.DEFAULT,
  'statistics': [],
  'type': DEVICE_TYPE.CPU,
};

const handleWorkerConnected = (workers, data) => {
  if (workers[data.worker]) {
    console.warn('duplicated worker found!! data will be overridden.', data.worker);
  }
  const worker = _.cloneDeep(WORKER_TEMPLATE);
  worker.device = data.name;
  worker.id = data.worker;
  worker.ip = data.ip;
  worker.platform = data.platform;
  worker.type = data.type;
  workers[data.worker] = worker;
};

const handleWorkerLost = (workers, data) => {
  delete workers[data.worker];
};

const handleStateChanged = (workers, data) => {
  const worker = workers[data.worker];
  if (!worker) {
    console.error('unknown worker id found', data.worker);
    return;
  }
  worker.state = data.state;
};

const handleGenerationResult = (workers, data) => {
  const worker = workers[data.worker];
  if (!worker) {
    console.error('unknown worker id found', data.worker);
    return;
  }
  worker.statistics.push(data.result);
  if (worker.best) {
    // TODO: we should read opt_for_max from server.
    worker.best = Math.min(worker.best, data.result.best_fitness);
  } else {
    worker.best = data.result.best_fitness;
  }
};

export default (state = initialState, payload) => {
  const data = payload.data;
  const workers = _.cloneDeep(state.workers);
  switch (payload.type) {
    case ACTION_KEYS.WORKER_CONNECTED:
      handleWorkerConnected(workers, data);
      return { workers };
    case ACTION_KEYS.WORKER_LOST:
      handleWorkerLost(workers, data);
      return { workers };
    case ACTION_KEYS.STATE_CHANGED:
      handleStateChanged(workers, data);
      return { workers };
    case ACTION_KEYS.GENERATION_RESULT:
      handleGenerationResult(workers, data);
      return { workers };
    default:
      return state;
  }
};
