import React, { PropTypes } from 'react';
import { DropdownButton, MenuItem } from 'react-bootstrap';

import { REPOPULATE_CONFIG_TYPE } from '../../shared/config';

export const getDropdownText = (type) => {
  switch(type) {
    case REPOPULATE_CONFIG_TYPE.DEFAULT:
      return 'Disabled';
    case REPOPULATE_CONFIG_TYPE.BEST_WORST_DIFF:
      return 'Diff of Best and Worst';
    case REPOPULATE_CONFIG_TYPE.BEST_AVG_DIFF:
      return 'Diff of Best and Average';
    default:
      throw new Error('unknown type: ' + type);
  }
}

const RepopulateTypeDropdown = (props) => {
  return (
    <DropdownButton bsStyle='default' title={getDropdownText(props.value)}
                    className={props.className} id='repopulate-type'
                    onSelect={props.onSelect}>
      <MenuItem eventKey={REPOPULATE_CONFIG_TYPE.DEFAULT}>
        {getDropdownText(REPOPULATE_CONFIG_TYPE.DEFAULT)}
      </MenuItem>
      <MenuItem eventKey={REPOPULATE_CONFIG_TYPE.BEST_WORST_DIFF}>
        {getDropdownText(REPOPULATE_CONFIG_TYPE.BEST_WORST_DIFF)}
      </MenuItem>
      <MenuItem eventKey={REPOPULATE_CONFIG_TYPE.BEST_AVG_DIFF}>
        {getDropdownText(REPOPULATE_CONFIG_TYPE.BEST_AVG_DIFF)}
      </MenuItem>
    </DropdownButton>
  );
};

RepopulateTypeDropdown.propTypes = {
  value: PropTypes.string,
  onSelect: PropTypes.func
}

export default RepopulateTypeDropdown;
