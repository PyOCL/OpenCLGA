import React, { Component, PropTypes } from 'react';
import NumericInput from 'react-numeric-input';
import RepopulateTypeDropdown from './repopulate_type_dropdown';
import { REPOPULATE_CONFIG_TYPE } from '../../shared/config';

class RepopulationRow extends Component {

  render() {
    const {
      className,
      config,
      onInputChange,
      onTypeChange
    } = this.props;
    const inputDisabled = config.type === REPOPULATE_CONFIG_TYPE.DISABLED;
    return (
      <div className={`${className}-row`}>
        <label>Repopulate 90% when</label>
        <RepopulateTypeDropdown value={config.type}
                                className={`type-dropdown ${className}-dropdown`}
                                onSelect={onTypeChange} />
        <label>is greater than</label>
        <div style={{display: 'inline-block'}}>
          <NumericInput className={`numeric-input ${className}-number`}
                        min={0.1} max={1000} value={config.diff} step={1}
                        onChange={onInputChange} disabled={inputDisabled} />
        </div>
      </div>
    );
  }
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
