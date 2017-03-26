import React, { PropTypes } from 'react';
import { Well } from 'react-bootstrap';
import LabeledInfo from '../base/labeled_info';

const ConnectedClients = (props) => {
  return (
    <Well>
      <LabeledInfo baseClassName='connected-clients'
                   className={props.className}
                   info={props.count}
                   label='Connected Devices:'/>
    </Well>
  );
};

ConnectedClients.propTypes = {
  className: PropTypes.string,
  count: PropTypes.number.isRequired
};

export default ConnectedClients;
