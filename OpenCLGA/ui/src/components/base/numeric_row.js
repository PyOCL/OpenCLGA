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
                        min={props.min} max={props.max} value={props.value} step={props.step}
                        onChange={props.onChange} disabled={props.disabled} />
          <label>{props.trailing}</label>
      </Col>
    </Row>
  );
};

NumericRow.propTypes = {
  baseClassName: PropTypes.string,
  disabled: PropTypes.bool,
  label: PropTypes.node,
  max: PropTypes.number,
  min: PropTypes.number,
  onChange: PropTypes.func,
  step: PropTypes.number,
  trailing: PropTypes.node,
  value: PropTypes.number
};

NumericRow.defaultProps = {
  baseClassName: 'numeric',
  disabled: false,
  min: 0,
  max: 100,
  value: 0,
  step: 1
};

export default NumericRow;
