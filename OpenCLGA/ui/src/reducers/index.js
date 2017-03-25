import { combineReducers } from 'redux';
import config from './config';
import control from './control';
import socket from './socket';
import lastAction from './actions';

export default combineReducers({
  config,
  control,
  socket,
  lastAction
});
