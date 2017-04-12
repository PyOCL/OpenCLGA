import React, { PropTypes } from 'react';
import { Well } from 'react-bootstrap';
import _ from 'lodash';
import { AGGREGRATION_SECONDS } from '../../shared/constants';
import LineChart from './line_chart';

const ResultLineChart = (props) => {
  const result = _.map(props.aggregrated, (item, key) => {
    const groupDate = new Date();
    groupDate.setTime(key);
    return {
      ...item,
      index: groupDate.toLocaleTimeString()
    };
  });
  const title = `Average Performance (aggregrated by ${AGGREGRATION_SECONDS} secs):`;
  return (
    <Well>
      {title}<br/>
      <LineChart data={result}/>
    </Well>
  );
};

ResultLineChart.propTypes = {
  aggregrated: PropTypes.object.isRequired
};

export default ResultLineChart;
