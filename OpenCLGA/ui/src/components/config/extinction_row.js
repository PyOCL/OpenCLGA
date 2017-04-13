import React, { Component, PropTypes } from 'react';
import NumericInput from 'react-numeric-input';
import ExtinctionTypeDropdown from './extinction_type_dropdown';
import { EXTINCTION_CONFIG_TYPE } from '../../shared/config';

class ExtinctionRow extends Component {

  render() {
    const {
      className,
      config,
      disabled,
      onInputChange,
      onTypeChange
    } = this.props;
    const inputDisabled = config.type === EXTINCTION_CONFIG_TYPE.DISABLED || disabled;
    return (
      <div className={`${className}-row`}>
        <label>Extinct 90% populations when</label>
        <ExtinctionTypeDropdown value={config.type}
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

ExtinctionRow.propTypes = {
  className: PropTypes.string,
  disabled: PropTypes.bool,
  type: PropTypes.string,
  onSelect: PropTypes.func
};

ExtinctionRow.defaultProps = {
  className: 'repopulating'
};

export default ExtinctionRow;
