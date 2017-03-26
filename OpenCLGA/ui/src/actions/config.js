import { ACTION_KEYS } from '../shared/config';

const setConfig = (field, data) => {
  return {
    type: ACTION_KEYS.SET_CONFIG,
    data: { field, data }
  };
};

export const setCrossoverRatio = (value) => (setConfig('crossoverRatio', value));
export const setMutationRatio = (value) => (setConfig('mutationRatio', value));
export const setPopulations = (value) => (setConfig('populations', value));
export const setShareBestCount = (value) => (setConfig('shareBestCount', value));

export const setRepopulateConfig = (type, diff) => (dispatch, getState) => {
  const { repopulateConfig } = getState().config;
  dispatch(setConfig('repopulateConfig', {
    type: type || repopulateConfig.type,
    // please note, we view 0 as an invalid value that will be reset to default.
    diff: diff || repopulateConfig.diff
  }));
};

export const setRepopulateConfigType = (type) => {
  return setRepopulateConfig(type);
};

export const setRepopulateConfigDiff = (diff) => {
  return setRepopulateConfig(null, diff);
};

export const setTermination = (type, value) => (dispatch, getState) => {
  dispatch(setConfig('termination', {
    type,
    [type]: value
  }));
};
