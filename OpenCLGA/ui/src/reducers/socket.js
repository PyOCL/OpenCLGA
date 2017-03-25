import { DEVICE_TYPE, OPENCLGA_STATES } from '../shared/constants';
import { ACTION_KEYS } from '../shared/socket';

const initialState = {
  clients: {}
};

const CLIENT_TEMPLATE = {
  'best': null,
  'device': '',
  'ip': '',
  'platform': '',
  'state': OPENCLGA_STATES.DEFAULT,
  'statistics': [],
  'type': DEVICE_TYPE.CPU,
};

const handleClientConnected = (clients, data) => {
  if (clients[data.client]) {
    console.warn('duplicated client found!! data will be overridden.', data.client);
  }
  const client = { ...CLIENT_TEMPLATE };
  client.device = data.device;
  client.id = data.client;
  client.ip = data.ip;
  client.platform = data.platform;
  client.type = data.type;
  clients[data.client] = client;
};

const handleClientLost = (clients, data) => {
  delete clients[data.client];
};

const handleStateChanged = (clients, data) => {
  const client = clients[data.client];
  if (!client) {
    console.error('unknown client id found', data.client);
    return;
  }
  client.state = data.state;
};

const handleGenerationResult = (clients, data) => {
  const client = clients[data.client];
  if (!client) {
    console.error('unknown client id found', data.client);
    return;
  }
  client.statistics.push(data.result);
  if (client.best) {
    // TODO: we should read opt_for_max from server.
    client.best = Math.min(client.best, data.result.best_fitness);
  } else {
    client.best = data.result.best_fitness;
  }
};

export default (state = initialState, payload) => {
  const data = payload.data;
  const clients = { ...state.clients };
  switch (payload.type) {
    case ACTION_KEYS.CLIENT_CONNECTED:
      handleClientConnected(clients, data);
      return { clients };
    case ACTION_KEYS.CLIENT_LOST:
      handleClientLost(clients, data);
      return { clients };
    case ACTION_KEYS.STATE_CHANGED:
      handleStateChanged(clients, data);
      return { clients };
    case ACTION_KEYS.GENERATION_RESULT:
      handleGenerationResult(clients, data);
      return { clients };
    default:
      return state;
  }
};
