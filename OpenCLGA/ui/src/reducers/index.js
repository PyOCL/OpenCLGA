import { combineReducers } from 'redux';
import config from './config';
import control from './control';

export default combineReducers({
    config: config,
    control: control
});
