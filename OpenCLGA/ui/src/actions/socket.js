import _ from 'lodash';
import { STATE_HANDLERS } from '../shared/constants';
import { ACTION_KEYS, WEBSOCKET_MESSAGE_TYPE } from '../shared/socket';
import { ACTION_KEYS as CONTROL_ACTION_KEYS } from '../shared/control';

class Socket {

  constructor() {
    this.listeners = {};
    this.updateGlobalState = this.updateGlobalState.bind(this);
  }

  on(type, listener) {
    const list = this.listeners[type] || [];
    list.push(listener);
  }

  init(store) {
    this.store = store;
    this.store.subscribe(this.updateGlobalState);
  }

  connect(url) {
    this.socket = new WebSocket(url);
    this.socket.addEventListener('open', this.handleOpen.bind(this));
    this.socket.addEventListener('close', this.handleClose.bind(this));
    this.socket.addEventListener('message', this.handleMessage.bind(this));
    this.socket.addEventListener('error', this.handleError.bind(this));
  }

  sendCommand(command, payload) {
    if (!this.connected) {
      return;
    }
    this.socket.send(JSON.stringify({ command, payload }));
  }

  handleOpen(evt) {
    this.connected = true;
    this.dispatchEvent('open', this);
  }

  handleClose(evt) {
    this.connected = false;
    this.dispatchEvent('close', {
      code: evt.code,
      reason: evt.reason
    });
  }

  // This is not a traditional action creator. It calculates the state and generates the
// action if needed. If no needs, it returns null.
  calcStateChange(currentState, clientsStates) {
    const nextState = STATE_HANDLERS[currentState](clientsStates);
    return (nextState !== currentState)
           ? { type: CONTROL_ACTION_KEYS.SET_STATE, data: nextState } : null;
  }

  updateGlobalState() {
    const states = this.store.getState();
    // We only care state changed
    if (states.lastAction.type !== ACTION_KEYS.STATE_CHANGED) {
      return;
    }

    const currentState = states.control.currentState;
    const clientsStates = _.map(states.socket.clients, (client) => {
      return client.state;
    });
    // We use control's calcStateChange function to check
    // if we need to dispatch a state change event.
    const action = this.calcStateChange(currentState, clientsStates);
    action && this.store.dispatch(action);
  }

  handleMessage(evt) {
    // TODO: to prevent information leakage, we should remove this line.
    console.log('ws msg', evt.data);
    if (!evt.data) {
      console.error('Wrong ws message got!!', evt);
      return;
    }
    const data = JSON.parse(evt.data);
    let actionType;
    switch (data.type) {
      case WEBSOCKET_MESSAGE_TYPE.CLIENT_CONNECTED:
        actionType = ACTION_KEYS.CLIENT_CONNECTED;
        break;
      case WEBSOCKET_MESSAGE_TYPE.CLIENT_LOST:
        actionType = ACTION_KEYS.CLIENT_LOST;
        break;
      case WEBSOCKET_MESSAGE_TYPE.STATE_CHANGED:
        actionType = ACTION_KEYS.STATE_CHANGED;
        break;
      case WEBSOCKET_MESSAGE_TYPE.GENERATION_RESULT:
        actionType = ACTION_KEYS.GENERATION_RESULT;
        break;
      default:
        console.log('Unknown ws message!!', data.type);
    }
    if (!actionType) {
      // no action type found!!
      return;
    }

    this.store.dispatch({
      type: actionType,
      payload: data.payload
    });
  }

  handleError(err) {
    console.error('websocket error', err);
  }

  dispatchEvent(type, data) {
    const listeners = this.listeners[type];
    if (!listeners || !listeners.length) {
      return;
    }

    listeners.forEach((item) => {
      try {
        typeof item === 'function' && item(data);
      } catch (ex) {
        console.error('error while fire event', type, ex);
      }
    });
  }
}

const singleton = new Socket();

export default singleton;
