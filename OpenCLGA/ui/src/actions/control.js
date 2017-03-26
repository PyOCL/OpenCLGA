import { OPENCLGA_STATES } from '../shared/constants';
import { createSimpleAction } from '../shared/utils';
import { ACTION_KEYS } from '../shared/control';
import socket from './socket';

const setState = createSimpleAction(ACTION_KEYS.SET_STATE);

export const prepare = () => (dispatch, getState) => {
  dispatch(setState(OPENCLGA_STATES.PREPARING));
  setTimeout(() => {
    dispatch(setState(OPENCLGA_STATES.PREPARED));
  }, 2000);
};

export const run = () => (dispatch, getState) => {
  socket.sendCommand('run', {
    'prob_mutation': 0.1,
    'prob_crossover': 0.8
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
