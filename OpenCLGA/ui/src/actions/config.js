import { ACTION_KEYS } from '../shared/config';

const setConfig = (field, data) => {
  return {
    type: ACTION_KEYS.SET_CONFIG,
    data: { field, data }
  };
};

export const setCrossoverRatio = (value) => (setConfig('crossoverRatio', value));
export const setMutationRatio = (value) => (setConfig('mutationRatio', value));
export const setPopulation = (value) => (setConfig('population', value));
export const setElitismMode = (value) => (setConfig('elitismMode', value));

export const setExtinctionCnfig = (type, diff) => (dispatch, getState) => {
  const { extinctionConfig } = getState().config;
  dispatch(setConfig('extinctionConfig', {
    type: type || extinctionConfig.type,
    // please note, we view 0 as an invalid value that will be reset to default.
    diff: diff || extinctionConfig.diff
  }));
};

export const setExtinctionConfigType = (type) => {
  return setExtinctionCnfig(type);
};

export const setExtinctionConfigDiff = (diff) => {
  return setExtinctionCnfig(null, diff);
};

export const setTermination = (type, value) => (dispatch, getState) => {
  dispatch(setConfig('termination', {
    type,
    [type]: value
  }));
};
