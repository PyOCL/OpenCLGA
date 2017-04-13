import React, { PropTypes } from 'react';
import {
  Checkbox
} from 'react-bootstrap';
import NumericInput from 'react-numeric-input';

// TODO: make this as a stateful component because create a function inside render is an
// anti-pattern.
const ElitismModeRow = (props) => {
  const handleCheckboxChanged = (evt) => {
    const value = props.value || 1;
    props.onChange(evt.target.checked ? value : 0);
  };
  return (
    <div className={`${props.className}-row`}>
      <Checkbox checked={props.value > 0} disabled={props.disabled} onChange={handleCheckboxChanged}>
        Share best results after
      </Checkbox>
      <NumericInput className={`numeric-input ${props.className}-number`}
                    disabled={props.disabled}
                    min={0} max={100000} value={props.value} step={1}
                    onChange={props.onChange}/>
      <label>generations.</label>
    </div>
   );
};

ElitismModeRow.propTypes = {
  className: PropTypes.string,
  disabled: PropTypes.bool,
  type: PropTypes.string,
  onSelect: PropTypes.func,
  onChange: PropTypes.func
};

ElitismModeRow.defaultProps = {
  className: 'elitism-mode'
};

export default ElitismModeRow;
