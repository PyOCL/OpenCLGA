import React, { Component, PropTypes } from 'react';
import NumericInput from 'react-numeric-input';
import RepopulatingTypeDropdown from './repopulating_type_dropdown';
import { REPOPULATING_CONFIG_TYPE } from '../../shared/config';

class RepopulatingRow extends Component {

  render() {
    const {
      className,
      config,
      disabled,
      onInputChange,
      onTypeChange
    } = this.props;
    const inputDisabled = config.type === REPOPULATING_CONFIG_TYPE.DISABLED || disabled;
    return (
      <div className={`${className}-row`}>
        <label>Repopulate 90% when</label>
        <RepopulatingTypeDropdown value={config.type}
                                  className={`type-dropdown ${className}-dropdown`}
                                  disabled={disabled}
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

RepopulatingRow.propTypes = {
  className: PropTypes.string,
  disabled: PropTypes.bool,
  type: PropTypes.string,
  onSelect: PropTypes.func
};

RepopulatingRow.defaultProps = {
  className: 'repopulating'
};

export default RepopulatingRow;
