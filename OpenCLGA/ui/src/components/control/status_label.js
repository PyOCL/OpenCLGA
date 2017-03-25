import React from 'react';
import LabeledInfo from '../base/labeled_info';

const StatusLabel = (props) => {
  return (<LabeledInfo baseClassName='status'
                       className={props.className}
                       info={props.status}
                       label='Status:' />);
};

export default StatusLabel;
