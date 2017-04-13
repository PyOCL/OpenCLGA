import _ from 'lodash';
import { createSimpleAction } from '../shared/utils';
import { EXTINCTION_CONFIG_TYPE } from '../shared/config';
import { ACTION_KEYS } from '../shared/control';
import socket from './socket';

export const setState = createSimpleAction(ACTION_KEYS.SET_STATE);

export const prepare = () => (dispatch, getState) => {
  const config = _.cloneDeep(getState().config);
  // The python uses seconds as its unit but we want to use minutes in UI.
  if (config.termination.type === 'time') {
    config.termination.time *= 60;
  }

  const options = {
    'termination': config.termination,
    'population': config.population,
    'prob_mutation': config.mutationRatio / 100,
    'prob_crossover': config.crossoverRatio / 100
  };

  if (config.extinctionConfig.type !== EXTINCTION_CONFIG_TYPE.DISABLED) {
    options['extinction'] = {
      type: config.extinctionConfig.type,
      diff: config.extinctionConfig.diff,
      ratio: 0.9
    }
  }

  if (config.elitismMode) {
    options['elitism_mode'] = config.elitismMode;
  }

  socket.sendCommand('prepare', options);
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
