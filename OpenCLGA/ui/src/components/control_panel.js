import React, { Component } from 'react';
import {
  Button,
  Panel,
  Row
} from 'react-bootstrap';

import StatusLabel from './control/status_label';

class ConfigPanel extends Component {

  render() {
    return (
      <Panel header='Control Panel' bsStyle='success'>
        <Row>
          <StatusLabel/>
          <div className='control-buttons'>
            <Button>Prepare</Button>
            <Button>Start</Button>
            <Button>Stop</Button>
            <Button>Pause</Button>
            <Button>Resume</Button>
          </div>
        </Row>
      </Panel>
    );
  }
}

export default ConfigPanel;
