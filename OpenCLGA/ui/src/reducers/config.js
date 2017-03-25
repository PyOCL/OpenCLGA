import { REPOPULATE_CONFIG_TYPE } from '../shared/config';

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

const AUTO_FILL_NAME = [
  'termination',
  'population',
  'mutationRatio',
  'crossoverRatio',
  'repopulateConfig',
  'shareBestCount'
];

export default (state = initialState, payload) => {
  if (AUTO_FILL_NAME.indexOf(payload.type) > -1) {
    return {
      ...state,
      [payload.type]: payload.data
    };
  } else {
    return state;
  }
};
