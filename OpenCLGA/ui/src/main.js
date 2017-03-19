import React, { Component } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { setRepopulateConfigType } from './actions/config';
import ConfigPanel from './components/config_panel';

import './styles/main.css';

class Main extends Component {
  render() {
    const {
      config,
      actions
    } = this.props;

    return (
      <div className='app'>
        <div className='app-header'>
          <h2>OpenCLGA UI</h2>
        </div>
        <div className='app-main'>
          <ConfigPanel config={config} actions={actions}/>
        </div>
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  return {
    config: state.config
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    actions: {
      setRepopulateConfigType: bindActionCreators(setRepopulateConfigType, dispatch)
    }
  }
};

export default connect(mapStateToProps, mapDispatchToProps)(Main);
