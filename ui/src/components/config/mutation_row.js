import React from 'react';
import NumericRow from '../base/numeric_row';

const MutationRow = (props) => {
  return (
    <NumericRow baseClassName='mutation'
                label='Mutation ratio:'
                trailing='%'
                min={1} max={100} value={20} step={1} />
  );
};

export default MutationRow;
