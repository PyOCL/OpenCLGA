import React, { PropTypes } from 'react';
import {
  Checkbox
} from 'react-bootstrap';
import NumericInput from 'react-numeric-input';

const ShareResultRow = (props) => {
  return (
    <div className={`${props.className}-row`}>
      <Checkbox>Share best results after</Checkbox>
      <NumericInput className={`numeric-input ${props.className}-number`}
                    min={1} max={100000} value={100} step={1} />
      <label>generations.</label>
    </div>
   );
};

ShareResultRow.propTypes = {
  className: PropTypes.string,
  type: PropTypes.string,
  onSelect: PropTypes.func
};

ShareResultRow.defaultProps = {
  className: 'share-result'
};

export default ShareResultRow;


