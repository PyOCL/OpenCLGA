import React, { PropTypes } from 'react';
import NumericInput from 'react-numeric-input';
import RepopulateTypeDropdown from './repopulate_type_dropdown';

const RepopulationRow = (props) => {
  return (
    <div className={`${props.className}-row`}>
      <label>Repopulate 90% when</label>
      <RepopulateTypeDropdown value={props.type}
                              className={`type-dropdown ${props.className}-dropdown`}
                              onSelect={props.onSelect} />
      <label>is greater than</label>
      <div style={{display: 'inline-block'}}>
        <NumericInput className={`numeric-input ${props.className}-number`}
                      min={0.1} max={1000} value={1} step={1} />
      </div>
    </div>
   );
};

RepopulationRow.propTypes = {
  className: PropTypes.string,
  type: PropTypes.string,
  onSelect: PropTypes.func
};

RepopulationRow.defaultProps = {
  className: 'repopulation'
};

export default RepopulationRow;
