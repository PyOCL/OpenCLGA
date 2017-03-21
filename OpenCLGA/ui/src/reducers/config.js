import { REPOPULATE_CONFIG_TYPE } from '../shared/config';

const initialState = {
  repopulateConfig: {
    type: REPOPULATE_CONFIG_TYPE.DEFAULT,
    diff: 0
  },
  shareBestCount: 0
};

export default (state = initialState, payload) => {
  switch (payload.type) {
    case 'setRepopulateConfig':
      return {
        ...state,
        repopulateConfig: payload.data
      };
    case 'setRepopulateConfigType':
      return {
        ...state,
        repopulateConfig: {
          ...state.repopulateConfig,
          type: payload.data
        }
      }
    case 'setShareBestCount':
      return {
        ...state,
        shareBestCount: payload.data
      };
    default:
      return state;
  }
};
