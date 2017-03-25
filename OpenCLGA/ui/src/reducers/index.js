import { combineReducers } from 'redux';
import config from './config';
import control from './control';
import socket from './socket';

export default combineReducers({
    config: config,
    control: control,
    socket: socket
});
