import React, { PropTypes } from 'react';
import { DropdownButton, MenuItem } from 'react-bootstrap';

import { REPOPULATING_CONFIG_TYPE } from '../../shared/config';

export const getDropdownText = (type) => {
  switch(type) {
    case REPOPULATING_CONFIG_TYPE.DISABLED:
      return 'Disabled';
    case REPOPULATING_CONFIG_TYPE.BEST_WORST_DIFF:
      return 'Diff of Best and Worst';
    case REPOPULATING_CONFIG_TYPE.BEST_AVG_DIFF:
      return 'Diff of Best and Average';
    default:
      throw new Error('unknown type: ' + type);
  }
}

const RepopulatingTypeDropdown = (props) => {
  return (
    <DropdownButton bsStyle='default' title={getDropdownText(props.value)}
                    className={props.className} id='repopulating-type'
                    onSelect={props.onSelect}>
      <MenuItem eventKey={REPOPULATING_CONFIG_TYPE.DISABLED}>
        {getDropdownText(REPOPULATING_CONFIG_TYPE.DISABLED)}
      </MenuItem>
      <MenuItem eventKey={REPOPULATING_CONFIG_TYPE.BEST_WORST_DIFF}>
        {getDropdownText(REPOPULATING_CONFIG_TYPE.BEST_WORST_DIFF)}
      </MenuItem>
      <MenuItem eventKey={REPOPULATING_CONFIG_TYPE.BEST_AVG_DIFF}>
        {getDropdownText(REPOPULATING_CONFIG_TYPE.BEST_AVG_DIFF)}
      </MenuItem>
    </DropdownButton>
  );
};

RepopulatingTypeDropdown.propTypes = {
  value: PropTypes.string,
  onSelect: PropTypes.func
}

export default RepopulatingTypeDropdown;
