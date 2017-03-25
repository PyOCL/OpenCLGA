// This file is a hack to record the latest actions and payload
export default (state = null, payload) => {
  return {
    type: payload.type,
    data: payload.data
  };
};
