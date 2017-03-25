import { OPENCLGA_STATES } from '../shared/constants';
import { ACTION_KEYS } from '../shared/control';

// convenient functions
const createButtonStates = (prepare, run, pause, stop) => {
  return { prepare, run, pause, stop };
};


const STATE_BUTTON_MAPPING = {
  [OPENCLGA_STATES.WAITING]: createButtonStates(true, false, false, false),
  [OPENCLGA_STATES.PREPARING]: createButtonStates(false, false, false, false),
  [OPENCLGA_STATES.RESTORING]: createButtonStates(false, false, false, false),
  [OPENCLGA_STATES.PREPARED]: createButtonStates(false, true, false, false),
  [OPENCLGA_STATES.RUNNING]: createButtonStates(false, false, true, true),
  [OPENCLGA_STATES.PAUSING]: createButtonStates(false, false, false, false),
  [OPENCLGA_STATES.PAUSED]: createButtonStates(false, true, false, true),
  [OPENCLGA_STATES.SAVING]: createButtonStates(false, false, false, false),
  [OPENCLGA_STATES.STOPPING]: createButtonStates(false, false, false, false),
  [OPENCLGA_STATES.STOPPED]: createButtonStates(false, false, false, false)
};

const initialState = {
  currentState: OPENCLGA_STATES.DEFAULT,
  buttons: STATE_BUTTON_MAPPING[OPENCLGA_STATES.DEFAULT]
};

export default (state = initialState, payload) => {
  switch (payload.type) {
    case ACTION_KEYS.SET_STATE:
      return {
        ...state,
        currentState: payload.data,
        buttons: STATE_BUTTON_MAPPING[payload.data]
      };
    default:
      return state;
  }
};
