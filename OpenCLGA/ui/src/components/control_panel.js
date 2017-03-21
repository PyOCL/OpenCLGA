import React, { Component } from 'react';
import {
  Button,
  Panel,
  Row
} from 'react-bootstrap';

import StatusLabel from './control/status_label';

class ConfigPanel extends Component {

  render() {
    const {
      controlActions,
      control
    } = this.props;

    return (
      <Panel header='Control Panel' bsStyle='success'>
        <Row>
          <StatusLabel status={control.currentState}/>
          <div className='control-buttons'>
            <Button disabled={!control.buttons.prepare}
                    onClick={controlActions.prepare}>
              Prepare
            </Button>
            <Button disabled={!control.buttons.run}
                    onClick={controlActions.run}>
              Run
            </Button>
            <Button disabled={!control.buttons.pause}
                    onClick={controlActions.pause}>
              Pause
            </Button>
            <Button disabled={!control.buttons.stop}
                    onClick={controlActions.stop}>
              Stop
            </Button>
          </div>
        </Row>
      </Panel>
    );
  }
}

export default ConfigPanel;
