import React, { Component } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { setRepopulateConfigType } from './actions/config';
import * as controlActions from './actions/control';
import ConfigPanel from './components/config_panel';
import ControlPanel from './components/control_panel';

import './styles/main.css';

class Main extends Component {
  render() {
    const {
      config,
      control,
      actions
    } = this.props;

    return (
      <div className='app'>
        <div className='app-header'>
          <h2>OpenCLGA UI</h2>
        </div>
        <div className='app-main'>
          <ConfigPanel config={config} actions={actions} />
          <ControlPanel control={control} actions={actions.controlActions} />
        </div>
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    config: state.config,
    control: state.control
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    actions: {
      setRepopulateConfigType: bindActionCreators(setRepopulateConfigType, dispatch),
      controlActions: bindActionCreators(controlActions, dispatch)
    }
  }
};

export default connect(mapStateToProps, mapDispatchToProps)(Main);
