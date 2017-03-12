import React, { Component } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { ButtonToolbar } from 'react-bootstrap';
import { setRepopulateConfigType } from './actions/config';
import RepopulateTypeDropdown from './components/repopulate_type_dropdown';

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
          <h2>oclGA UI</h2>
        </div>
        <div className='app-main'>
          <ButtonToolbar>
            <RepopulateTypeDropdown value={config.repopulateConfig.type}
                                    onSelect={actions.setRepopulateConfigType} />
          </ButtonToolbar>
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
