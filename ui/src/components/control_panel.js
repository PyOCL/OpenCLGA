import React, { Component } from 'react';
import {
  Panel,
  Row
} from 'react-bootstrap';

class ConfigPanel extends Component {

  render() {
    return (
      <Panel header='Control Panel' bsStyle='success'>
        <Row>
          ABCDEFG
        </Row>
      </Panel>
    );
  }
}

export default ConfigPanel;
