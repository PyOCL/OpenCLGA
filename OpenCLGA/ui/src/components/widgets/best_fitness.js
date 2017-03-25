import React, { PropTypes } from 'react';
import { Well } from 'react-bootstrap';
import numeral from 'numeral';
import LabeledInfo from '../base/labeled_info';

const BestFitness = (props) => {
  const content = numeral(props.value).format('0,0.0000');
  return (
    <Well>
      <LabeledInfo baseClassName='best-fitness'
                   className={props.className}
                   info={content}
                   label='Best:' />
    </Well>
  );
};

BestFitness.propTypes = {
  className: PropTypes.string,
  value: PropTypes.number.isRequired
};

export default BestFitness;
