import React, { PropTypes } from 'react';
import {
  Col,
  ControlLabel,
  Row
} from 'react-bootstrap';
import NumericInput from 'react-numeric-input';

const NumericRow = (props) => {
  return (
    <Row className={`${props.baseClassName}-row`}>
      <Col xs={12} sm={4} md={4}><ControlLabel>{props.label}</ControlLabel></Col>
      <Col xs={12} sm={8} md={8}>
          <NumericInput className={`${props.baseClassName}-number`}
                        min={props.min} max={props.max} value={props.value} step={props.step} />
          {props.trailing}
      </Col>
    </Row>
  );
};

NumericRow.propTypes = {
  baseClassName: PropTypes.string,
  label: PropTypes.node,
  trailing: PropTypes.node,
  min: PropTypes.number,
  max: PropTypes.number,
  value: PropTypes.number,
  step: PropTypes.number
};

NumericRow.defaultProps = {
  baseClassName: 'numeric',
  min: 0,
  max: 100,
  value: 0,
  step: 1
};

export default NumericRow;
