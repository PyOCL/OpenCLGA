import React from 'react';
import NumericRow from '../base/numeric_row';

const PopulationRow = (props) => {
  return (
    <NumericRow baseClassName='population'
                disabled={props.disabled}
                label='Population per Device:'
                min={100} value={props.value} max={1000000000} step={100}
                onChange={props.onChange}/>
  );
};

export default PopulationRow;
