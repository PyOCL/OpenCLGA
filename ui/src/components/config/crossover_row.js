import React from 'react';
import NumericRow from '../base/numeric_row';

const CrossoverRow = (props) => {
  return (
    <NumericRow baseClassName='crossover'
                label='Crossover ratio:'
                trailing='%'
                min={1} max={100} value={80} step={1} />
  );
};

export default CrossoverRow;
