
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
        this.dispatch('open', this);
    }

    handleClose(evt) {
        this.connected = false;
        this.dispatch('close', {
            code: evt.code,
            reason: evt.reason
        });
    }

    handleMessage(evt) {
        console.log('ws message', evt.data);
    }

    handleError(err) {
        console.error('websocket error', err);
    }

    dispatch(type, data) {
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
