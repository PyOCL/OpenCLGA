import React, { Component } from 'react';
import {
  Col,
  ControlLabel,
  Radio,
  Row
} from 'react-bootstrap';
import NumericInput from 'react-numeric-input';

class GenerationsRow extends Component {
  render() {
    return (
      <Row className='generations-row'>
        <Col xs={12} sm={4} md={4}><ControlLabel>Generations:</ControlLabel></Col>
        <Col xs={12} sm={8} md={8}>
          <div>
            <Radio name='generationType'>By count:</Radio>
            <NumericInput className='generations-count-number'
                          min={1} value={1000} step={1000}/>
          </div>
          <div>
            <Radio name='generationType'>By time:</Radio>
            <NumericInput className='generations-time-number'
                          min={1} value={10}/>mins
          </div>
        </Col>
      </Row>
    );
  }
}

export default GenerationsRow;
