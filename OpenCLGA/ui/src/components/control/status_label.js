import React from 'react';
import { Row } from 'react-bootstrap';

const StatusLabel = (props) => {
  return (
    <Row className='status-label-row'>
      <Row className='label-row'>Status:</Row>
      <Row className='status-row'>{props.currentState}</Row>
    </Row>
  );
}

export default StatusLabel;
