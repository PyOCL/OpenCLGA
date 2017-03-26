import React, { Component } from 'react';
import { Col, Row } from 'react-bootstrap';
import _ from 'lodash';

import ConnectedWorkers from './widgets/connected_workers';
import BestFitness from './widgets/best_fitness';
import WorkersTable from './widgets/workers_table';

class WidgetsPanel extends Component {

  render() {
    const {
      workers
    } = this.props;

    const bestResult = _.min(_.map(workers, (item) => (item.best))) || 0;
    let sortedWorkerArray = _.sortBy(_.values(workers), 'id');
    sortedWorkerArray = sortedWorkerArray.map((item) => {
      item.generationCount = item.statistics.length;
      return item;
    });
    return (
      <div className='widget-panel'>
        <Row className='widgets-panel-row'>
          <Col xs={12} sm={12} md={6}>
            <ConnectedWorkers count={_.size(workers)} />
          </Col>
          <Col xs={12} sm={12} md={6}>
            <BestFitness value={bestResult} />
          </Col>
        </Row>
        <Row className='widgets-panel-row'>
          <Col xs={12} sm={12} md={12}>
            <WorkersTable workers={sortedWorkerArray} />
          </Col>
        </Row>
      </div>
    );
  }
};

export default WidgetsPanel;
