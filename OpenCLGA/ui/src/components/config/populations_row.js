import React from 'react';
import NumericRow from '../base/numeric_row';

const PopulationsRow = (props) => {
  return (
    <NumericRow baseClassName='populations'
                label='Populations per Device:'
                min={100} value={props.value} max={1000000000} step={100}
                onChange={props.onChange}/>
  );
};

export default PopulationsRow;
