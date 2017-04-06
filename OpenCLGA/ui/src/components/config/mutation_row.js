import React from 'react';
import NumericRow from '../base/numeric_row';

const MutationRow = (props) => {
  return (
    <NumericRow baseClassName='mutation'
                disabled={props.disabled}
                label='Mutation ratio (%):'
                min={1} max={100} value={props.value} step={1}
                onChange={props.onChange}/>
  );
};

export default MutationRow;
