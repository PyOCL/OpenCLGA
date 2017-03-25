import { ACTION_KEYS, WEBSOCKET_MESSAGE_TYPE } from '../shared/socket';

class Socket {

    constructor() {
        this.listeners = {};
    }

    on(type, listener) {
        const list = this.listeners[type] || [];
        list.push(listener);
    }

    init(store) {
        this.store = store;
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
