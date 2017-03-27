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
export const setShareBestCount = (value) => (setConfig('shareBestCount', value));

export const setRepopulatingConfig = (type, diff) => (dispatch, getState) => {
  const { repopulatingConfig } = getState().config;
  dispatch(setConfig('repopulatingConfig', {
    type: type || repopulatingConfig.type,
    // please note, we view 0 as an invalid value that will be reset to default.
    diff: diff || repopulatingConfig.diff
  }));
};

export const setRepopulatingConfigType = (type) => {
  return setRepopulatingConfig(type);
};

export const setRepopulatingConfigDiff = (diff) => {
  return setRepopulatingConfig(null, diff);
};

export const setTermination = (type, value) => (dispatch, getState) => {
  dispatch(setConfig('termination', {
    type,
    [type]: value
  }));
};
