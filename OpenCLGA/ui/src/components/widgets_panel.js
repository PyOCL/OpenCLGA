import React, { Component } from 'react';
import { Col, Row } from 'react-bootstrap';
import _ from 'lodash';

import ConnectedClients from './widgets/connected_clients';
import BestFitness from './widgets/best_fitness';
import ClientsTable from './widgets/clients_table';

class WidgetsPanel extends Component {

  render() {
    const {
      clients
    } = this.props;

    const bestResult = _.min(_.map(clients, (item) => (item.best))) || 0;
    let sortedClientArray = _.sortBy(_.values(clients), 'id');
    sortedClientArray = sortedClientArray.map((item) => {
      item.generationCount = item.statistics.length;
      return item;
    });
    return (
      <div className='widget-panel'>
        <Row className='widgets-panel-row'>
          <Col xs={12} sm={12} md={6}>
            <ConnectedClients count={_.size(clients)} />
          </Col>
          <Col xs={12} sm={12} md={6}>
            <BestFitness value={bestResult} />
          </Col>
        </Row>
        <Row className='widgets-panel-row'>
          <Col xs={12} sm={12} md={12}>
            <ClientsTable clients={sortedClientArray} />
          </Col>
        </Row>
      </div>
    );
  }
};

export default WidgetsPanel;
