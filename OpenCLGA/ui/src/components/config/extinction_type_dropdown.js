import React, { PropTypes } from 'react';
import { DropdownButton, MenuItem } from 'react-bootstrap';

import { EXTINCTION_CONFIG_TYPE } from '../../shared/config';

export const getDropdownText = (type) => {
  switch(type) {
    case EXTINCTION_CONFIG_TYPE.DISABLED:
      return 'Disabled';
    case EXTINCTION_CONFIG_TYPE.BEST_WORST_DIFF:
      return 'Diff of Best and Worst';
    case EXTINCTION_CONFIG_TYPE.BEST_AVG_DIFF:
      return 'Diff of Best and Average';
    default:
      throw new Error('unknown type: ' + type);
  }
}

const ExtinctionTypeDropdown = (props) => {
  return (
    <DropdownButton bsStyle='default' title={getDropdownText(props.value)}
                    disabled={props.disabled}
                    className={props.className} id='repopulating-type'
                    onSelect={props.onSelect}>
      <MenuItem eventKey={EXTINCTION_CONFIG_TYPE.DISABLED}>
        {getDropdownText(EXTINCTION_CONFIG_TYPE.DISABLED)}
      </MenuItem>
      <MenuItem eventKey={EXTINCTION_CONFIG_TYPE.BEST_WORST_DIFF}>
        {getDropdownText(EXTINCTION_CONFIG_TYPE.BEST_WORST_DIFF)}
      </MenuItem>
      <MenuItem eventKey={EXTINCTION_CONFIG_TYPE.BEST_AVG_DIFF}>
        {getDropdownText(EXTINCTION_CONFIG_TYPE.BEST_AVG_DIFF)}
      </MenuItem>
    </DropdownButton>
  );
};

ExtinctionTypeDropdown.propTypes = {
  disabled: PropTypes.bool,
  value: PropTypes.string,
  onSelect: PropTypes.func
}

export default ExtinctionTypeDropdown;
