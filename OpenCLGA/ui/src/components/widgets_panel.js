import React, { Component } from 'react';
import { Col, Row } from 'react-bootstrap';
import _ from 'lodash';

import ConnectedDevices from './widgets/connected_devices';
import BestFitness from './widgets/best_fitness';

class WidgetsPanel extends Component {

  render() {
    const {
      clients
    } = this.props;

    const bestResult = _.min(_.map(clients, (item) => (item.best))) || 0;

    return (
      <Row className='widgets-panel'>
        <Col xs={12} sm={12} md={6}>
          <ConnectedDevices count={_.size(clients)} />
        </Col>
        <Col xs={12} sm={12} md={6}>
          <BestFitness value={bestResult} />
        </Col>
      </Row>
    );
  }
};

export default WidgetsPanel;
