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

const waitingState = (others) => {
  const allPreparing = others.every((state) => {
    return state === OPENCLGA_STATES.PREPARING || state === OPENCLGA_STATES.PREPARED;
  });
  const allRestoring = others.every((state) => {
    return state === OPENCLGA_STATES.RESTORING || state === OPENCLGA_STATES.PREPARED;
  });

  const allPrepared = others.every((state) => {
    return state === OPENCLGA_STATES.PREPARED;
  });

  if (allPreparing) {
    return OPENCLGA_STATES.PREPARING;
  } else if (allRestoring) {
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
  return others.every((state) => (state === OPENCLGA_STATES.RUNNING))
              ? OPENCLGA_STATES.RUNNING : OPENCLGA_STATES.PREPARED;
};

const runningState = (others) => {
  const allPausing = others.every((state) => {
    return state === OPENCLGA_STATES.PAUSING || state === OPENCLGA_STATES.PAUSED;
  });
  const allStopping = others.every((state) => {
    return state === OPENCLGA_STATES.STOPPING || state === OPENCLGA_STATES.STOPPED;
  });
  const allPaused = others.every((state) => {
    return state === OPENCLGA_STATES.PAUSED;
  });
  const allStopped = others.every((state) => {
    return state === OPENCLGA_STATES.STOPPED;
  });

  if (allPausing) {
    return OPENCLGA_STATES.PAUSING;
  } else if (allStopping) {
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
  const allRunning = others.every((state) => (state === OPENCLGA_STATES.RUNNING));
  const allSaving = others.every((state) => (state === OPENCLGA_STATES.SAVING));
  return allRunning ? OPENCLGA_STATES.RUNNING
                    : (allSaving ? OPENCLGA_STATES.SAVING : OPENCLGA_STATES.PAUSED);
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

