import _ from 'lodash';
import { OPENCLGA_STATES } from '../shared/constants';
import { createSimpleAction } from '../shared/utils';
import { ACTION_KEYS } from '../shared/control';
import socket from './socket';

const setState = createSimpleAction(ACTION_KEYS.SET_STATE);

export const prepare = () => (dispatch, getState) => {
  const config = _.cloneDeep(getState().config);
  // The python uses seconds as its unit but we want to use minutes in UI.
  if (config.termination.type === 'time') {
    config.termination.time *= 60;
  }
  socket.sendCommand('prepare', {
    'termination': config.termination,
    'population': config.population,
    'prob_mutation': config.mutationRatio / 100,
    'prob_crossover': config.crossoverRatio / 100,
    'repopulating': {
      type: config.repopulatingConfig.type,
      diff: config.repopulatingConfig.diff
    },
    'sharing_best_after': config.shareBestCount
  });
};

export const run = () => (dispatch, getState) => {
  const config = getState().config;
  socket.sendCommand('run', {
    'prob_mutation': config.mutationRatio / 100,
    'prob_crossover': config.crossoverRatio / 100
  });
};

export const pause = () => (dispatch, getState) => {
  socket.sendCommand('pause');
};

export const stop = () => (dispatch, getState) => {
  socket.sendCommand('stop');
};
