import { OPENCLGA_STATES } from '../shared/constants';
import { createSimpleAction } from '../shared/utils';
import { ACTION_KEYS } from '../shared/control';
import socket from './socket';

const setState = createSimpleAction(ACTION_KEYS.SET_STATE);

export const prepare = () => (dispatch, getState) => {
  const config = getState().config;
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

  setTimeout(() => {
    dispatch(setState(OPENCLGA_STATES.PREPARED));
  }, 2000);
};

export const run = () => (dispatch, getState) => {
  const config = getState().config;
  socket.sendCommand('run', {
    'prob_mutation': config.mutationRatio / 100,
    'prob_crossover': config.crossoverRatio / 100
  });
  // The following line should be removed. The state changing should be made by
  // socket... We use this line to easy testing.
  setTimeout(() => {
    dispatch(setState(OPENCLGA_STATES.RUNNING));
  }, 2000);
};

export const pause = () => (dispatch, getState) => {
  socket.sendCommand('pause');
  // The following line should be removed. The state changing should be made by
  // socket... We use this line to easy testing.
  setTimeout(() => {
    dispatch(setState(OPENCLGA_STATES.PAUSED));
  }, 2000);
};

export const stop = () => (dispatch, getState) => {
  socket.sendCommand('stop');
  // The following line should be removed. The state changing should be made by
  // socket... We use this line to easy testing.
  setTimeout(() => {
    dispatch(setState(OPENCLGA_STATES.STOPPED));
  }, 2000);
};
