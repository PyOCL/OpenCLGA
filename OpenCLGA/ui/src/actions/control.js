import { OPENCLGA_STATES } from '../shared/constants';
import { createSimpleAction } from '../shared/utils';
import { ACTION_KEYS } from '../shared/control';

const setState = createSimpleAction(ACTION_KEYS.setState);

export const prepare = () => (dispatch, getState) => {
    dispatch(setState(OPENCLGA_STATES.PREPARING));
    setTimeout(() => {
        dispatch(setState(OPENCLGA_STATES.PREPARED));
    }, 2000);
};

export const run = () => (dispatch, getState) => {
    dispatch(setState(OPENCLGA_STATES.RUNNING));
};

export const pause = () => (dispatch, getState) => {
    dispatch(setState(OPENCLGA_STATES.PAUSING));
    setTimeout(() => {
        dispatch(setState(OPENCLGA_STATES.PAUSED));
    }, 2000);
};

export const stop = () => (dispatch, getState) => {
    dispatch(setState(OPENCLGA_STATES.STOPPING));
    setTimeout(() => {
        dispatch(setState(OPENCLGA_STATES.STOPPED));
    }, 2000);
};
