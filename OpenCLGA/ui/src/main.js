import React, { Component } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import * as configActions from './actions/config';
import * as controlActions from './actions/control';
import ConfigPanel from './components/config_panel';
import ControlPanel from './components/control_panel';
import WidgetsPanel from './components/widgets_panel';
import WebSocketURLDialog from './components/dialogs/websocket_url_dialog';
import { DEFAULT_WEBSOCKET_SERVER } from './shared/constants';
import socket from './actions/socket';

import './styles/main.css';

const classNameMap = {
  'waiting': 'app loading',
  'connecting': 'app loading connecting',
  'connected': 'app'
};

class Main extends Component {

  constructor(props) {
    super(props);
    this.state = {
      url: null,
      state: 'waiting'
    };
    this.handleURLDialogClose = ::this.handleURLDialogClose;
    this.handleSocketConnected = ::this.handleSocketConnected;
    this.handleSocketError = ::this.handleSocketError;
    socket.on('open', this.handleSocketConnected);
    socket.on('error', this.handleSocketError);
  }

  componentDidMount() {
    if (DEFAULT_WEBSOCKET_SERVER !== 'dialog') {
      socket.connect();
      this.setState({ state: 'connecting' });
    }
  }

  handleSocketConnected() {
    this.setState({ state: 'connected' });
    socket.off('open', this.handleSocketConnected);
    socket.off('error', this.handleSocketError);
  }

  handleSocketError(error) {
    this.setState({ state: 'waiting' });
  }

  handleURLDialogClose(url) {
    if (!url) {
      return;
    }
    try {
      socket.connect(url);
      this.setState({ state: 'connecting' });
    } catch(ex) {
      console.error('websocket connecting error');
    }
  }

  render() {
    const {
      config,
      control,
      actions,
      aggregrated,
      workers
    } = this.props;

    const clsNames = classNameMap[this.state.state];
    return (
      <div className={clsNames}>
        <div className='app-header'>
          <h2>OpenCLGA UI</h2>
        </div>
        <div className='app-main'>
          <ConfigPanel config={config} state={control.currentState}
                       actions={actions.configActions} />
          <ControlPanel control={control} actions={actions.controlActions} />
          <WidgetsPanel aggregrated={aggregrated} workers={workers} />
          { DEFAULT_WEBSOCKET_SERVER === 'dialog' && this.state.state === 'waiting' &&
            <WebSocketURLDialog onClose={this.handleURLDialogClose} />
          }
        </div>
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    config: state.config,
    control: state.control,
    aggregrated: state.socket.aggregrated,
    workers: state.socket.workers
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    actions: {
      configActions: bindActionCreators(configActions, dispatch),
      controlActions: bindActionCreators(controlActions, dispatch)
    }
  }
};

export default connect(mapStateToProps, mapDispatchToProps)(Main);
