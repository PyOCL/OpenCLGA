import React, { PropTypes } from 'react';
import { Row } from 'react-bootstrap';

const LabeledInfo = (props) => {
  const className = props.className ? props.className : '';
  return (
    <Row className={props.baseClassName + '-label-row labeled-info-row ' + className}>
      <Row className='label-row'>{props.label}</Row>
      <Row className='info-row'>{props.info}</Row>
    </Row>
  );
}

LabeledInfo.propTypes = {
  baseClassName: PropTypes.string.isRequired,
  className: PropTypes.string,
  info: PropTypes.node.isRequired,
  label: PropTypes.node.isRequired,
};

export default LabeledInfo;
