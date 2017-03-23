import { createSimpleAction } from '../shared/utils';

export const setCrossoverRatio = createSimpleAction('crossoverRatio');
export const setMutationRatio = createSimpleAction('mutationRatio');
export const setPopulation = createSimpleAction('population');
export const setShareBestCount = createSimpleAction('shareBestCount');


const setConfig = (type, data) => {
    return { type, data };
};

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
