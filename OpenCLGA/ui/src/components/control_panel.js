import React, { Component } from 'react';
import {
  Button,
  Panel,
  Row
} from 'react-bootstrap';

import StatusLabel from './control/status_label';

class ControlPanel extends Component {

  render() {
    const {
      actions,
      control
    } = this.props;
    return (
      <Panel header='Control Panel' bsStyle='success'>
        <Row>
          <StatusLabel className={control.currentState} status={control.currentState}/>
          <div className='control-buttons'>
            <Button disabled={!control.buttons.prepare} onClick={actions.prepare}>
              Prepare
            </Button>
            <Button disabled={!control.buttons.run} onClick={actions.run}>
              Run
            </Button>
            <Button disabled={!control.buttons.pause} onClick={actions.pause}>
              Pause
            </Button>
            <Button disabled={!control.buttons.stop} onClick={actions.stop}>
              Stop
            </Button>
          </div>
        </Row>
      </Panel>
    );
  }
}

export default ControlPanel;
