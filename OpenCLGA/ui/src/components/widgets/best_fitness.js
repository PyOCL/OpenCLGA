import React, { PropTypes } from 'react';
import { Well } from 'react-bootstrap';
import LabeledInfo from '../base/labeled_info';
import { formatFitness } from '../../shared/utils';

const BestFitness = (props) => {
  const content = formatFitness(props.value);
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
