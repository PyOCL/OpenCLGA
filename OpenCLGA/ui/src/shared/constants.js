import _ from 'lodash';

export const OPENCLGA_STATES = {
  DEFAULT: 'waiting',
  WAITING: 'waiting',
  PREPARING: 'preparing',
  RESTORING: 'restoring',
  PREPARED: 'prepared',
  RUNNING: 'running',
  PAUSING: 'pausing',
  PAUSED: 'paused',
  SAVING: 'saving',
  STOPPING: 'stopping',
  STOPPED: 'stopped'
};

export const DEVICE_TYPE = {
  GPU: 'gpu',
  CPU: 'cpu',
  DSP: 'dsp'
};

// This is the default websocket connection information:
// The default websocket server may have the following candidates:
// 1. 'dialog': for showing an input dialog for connecting to any servers.
// 2. '[IP address]': for connecting to specified server
// 3. null: for connecting to localhost server
export const DEFAULT_WEBSOCKET_SERVER = null;
export const DEFAULT_WEBSOCKET_PORT = 8000;

const waitingState = (others) => {
  const anyPreparing = _.some(others, (state) => (state === OPENCLGA_STATES.PREPARING));
  const anyRestoring = _.some(others, (state) => (state === OPENCLGA_STATES.RESTORING));
  const allPrepared = others.every((state) => (state === OPENCLGA_STATES.PREPARED));

  if (anyPreparing) {
    return OPENCLGA_STATES.PREPARING;
  } else if (anyRestoring) {
    return OPENCLGA_STATES.RESTORING;
  } else if (allPrepared) {
    return OPENCLGA_STATES.PREPARED;
  }
};

const preparingState = (others) => {
  return others.every((state) => (state === OPENCLGA_STATES.PREPARED))
            ? OPENCLGA_STATES.PREPARED : OPENCLGA_STATES.PREPARING;
};

const restoringState = (others) => {
  return others.every((state) => (state === OPENCLGA_STATES.PREPARED))
              ? OPENCLGA_STATES.PREPARED : OPENCLGA_STATES.RESTORING;
};

const preparedState = (others) => {
  return _.some(others, (state) => (state === OPENCLGA_STATES.RUNNING))
              ? OPENCLGA_STATES.RUNNING : OPENCLGA_STATES.PREPARED;
};

const runningState = (others) => {
  const anyPausing = _.some(others, (state) => (state === OPENCLGA_STATES.PAUSING));
  const anyStopping = _.some(others, (state) => (state === OPENCLGA_STATES.STOPPING));
  const allPaused = others.every((state) => (state === OPENCLGA_STATES.PAUSED));
  const allStopped = others.every((state) => (state === OPENCLGA_STATES.STOPPED));

  if (anyPausing) {
    return OPENCLGA_STATES.PAUSING;
  } else if (anyStopping) {
    return OPENCLGA_STATES.STOPPING;
  } else if (allPaused) {
    return OPENCLGA_STATES.PAUSED;
  } else if (allStopped) {
    return OPENCLGA_STATES.STOPPED;
  } else {
    return OPENCLGA_STATES.RUNNING;
  }
};

const pausingState = (others) => {
  return others.every((state) => (state === OPENCLGA_STATES.PAUSED))
            ? OPENCLGA_STATES.PAUSED : OPENCLGA_STATES.PUASING;
};

const stoppingState = (others) => {
  return others.every((state) => (state === OPENCLGA_STATES.STOPPED))
              ? OPENCLGA_STATES.STOPPED : OPENCLGA_STATES.STOPPING;
};

const pausedState = (others) => {
  const anyRunning = _.some(others, (state) => (state === OPENCLGA_STATES.RUNNING));
  const anySaving = _.some(others, (state) => (state === OPENCLGA_STATES.SAVING));
  const anyStopping = _.some(others, (state) => (state === OPENCLGA_STATES.STOPPIG));
  if (anyRunning) {
    return OPENCLGA_STATES.RUNNING;
  } else if (anySaving) {
    return OPENCLGA_STATES.SAVING;
  } else if (anyStopping) {
    return OPENCLGA_STATES.STOPPING;
  } else {
    return OPENCLGA_STATES.PAUSED;
  }
}

const savingState = (others) => {
  const allPaused = others.every((state) => (state === OPENCLGA_STATES.PAUSED));
  return allPaused ? OPENCLGA_STATES.PAUSED : OPENCLGA_STATES.SAVING;
}

const stoppedState = (others) => {
  return OPENCLGA_STATES.STOPPED;
};

export const STATE_HANDLERS = {
  [OPENCLGA_STATES.WAITING]: waitingState,
  [OPENCLGA_STATES.PREPARING]: preparingState,
  [OPENCLGA_STATES.RESTORING]: restoringState,
  [OPENCLGA_STATES.PREPARED]: preparedState,
  [OPENCLGA_STATES.RUNNING]: runningState,
  [OPENCLGA_STATES.PAUSING]: pausingState,
  [OPENCLGA_STATES.PAUSED]: pausedState,
  [OPENCLGA_STATES.SAVING]: savingState,
  [OPENCLGA_STATES.STOPPING]: stoppingState,
  [OPENCLGA_STATES.STOPPED]: stoppedState
};

export const AGGREGRATION_SECONDS = 5;
