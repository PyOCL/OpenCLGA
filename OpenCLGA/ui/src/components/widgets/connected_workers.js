import React, { PropTypes } from 'react';
import { Well } from 'react-bootstrap';
import LabeledInfo from '../base/labeled_info';

const ConnectedWorkers = (props) => {
  return (
    <Well>
      <LabeledInfo baseClassName='connected-workers'
                   className={props.className}
                   info={props.count}
                   label='Connected Devices:'/>
    </Well>
  );
};

ConnectedWorkers.propTypes = {
  className: PropTypes.string,
  count: PropTypes.number.isRequired
};

export default ConnectedWorkers;
