export const WEBSOCKET_MESSAGE_TYPE = {
  STATE_CHANGED: 'stateChanged',
  CLIENT_CONNECTED: 'clientConnected',
  CLIENT_LOST: 'clientLost',
  GENERATION_RESULT: 'generationResult'
};

export const ACTION_KEYS = {
    clientConnected: WEBSOCKET_MESSAGE_TYPE.CLIENT_CONNECTED,
    clientLost: WEBSOCKET_MESSAGE_TYPE.CLIENT_LOST,
    stateChanged: WEBSOCKET_MESSAGE_TYPE.STATE_CHANGED,
    generationResult: WEBSOCKET_MESSAGE_TYPE.GENERATION_RESULT
};
