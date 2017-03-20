import React from 'react';
import { Row } from 'react-bootstrap';

const StatusLabel = () => {
  return (
    <Row className='status-label-row'>
      <Row className='label-row'>Status:</Row>
      <Row className='status-row'>Waiting</Row>
    </Row>
  );
}

export default StatusLabel;
