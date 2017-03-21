import React from 'react';
import { Row } from 'react-bootstrap';

const StatusLabel = (props) => {
  return (
    <Row className={'status-label-row ' + (props.className ? props.className : '')}>
      <Row className='label-row'>Status:</Row>
      <Row className='status-row'>{props.status}</Row>
    </Row>
  );
}

export default StatusLabel;
