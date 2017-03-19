import React from 'react';
import NumericRow from '../base/numeric_row';

const PopulationsRow = (props) => {
  return (
    <NumericRow baseClassName='populations'
                label='Populations per Device:'
                min={100} value={1000} step={1000} />
  );
};

export default PopulationsRow;
