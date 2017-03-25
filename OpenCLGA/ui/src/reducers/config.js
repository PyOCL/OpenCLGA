import { ACTION_KEYS, REPOPULATE_CONFIG_TYPE } from '../shared/config';

const initialState = {
  termination: {
    type: 'count',
    count: 1000
  },
  population: 100,
  mutationRatio: 10,
  crossoverRatio: 80,
  repopulateConfig: {
    type: REPOPULATE_CONFIG_TYPE.DEFAULT,
    diff: 1
  },
  shareBestCount: 0
};

export default (state = initialState, payload) => {
  if (ACTION_KEYS.SET_CONFIG === payload.type) {
    return {
      ...state,
      [payload.data.field]: payload.data.data
    };
  } else {
    return state;
  }
};
