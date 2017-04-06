import React from 'react';
import NumericRow from '../base/numeric_row';

const CrossoverRow = (props) => {
  return (
    <NumericRow baseClassName='crossover'
                disabled={props.disabled}
                label='Crossover ratio (%):'
                min={1} max={100} value={props.value} step={1}
                onChange={props.onChange} />
  );
};

export default CrossoverRow;
