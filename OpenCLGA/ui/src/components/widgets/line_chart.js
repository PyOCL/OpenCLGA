import React, { PropTypes } from 'react';
import {
  Brush,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

const FitnessLineChart = (props) => {
  return (
    <ResponsiveContainer height={300} width='100%'>
      <LineChart className={props.className} data={props.data}
                 margin={{top: 10, right: 0, left: 0, bottom: 0}}>
        <XAxis dataKey='index'/>
        <YAxis/>
        <CartesianGrid strokeDasharray="3 3"/>
        <Tooltip/>
        <Line dataKey='best_fitness'
              dot={false}
              fill='#8884d8'
              isAnimationActive={false}
              stroke='#8884d8'
              type='natural'/>
        <Line dataKey='avg_fitness'
              dot={false}
              fill='#82ca9d'
              isAnimationActive={false}
              stroke='#82ca9d'
              type='natural'/>
        <Line dataKey='worst_fitness'
              dot={false}
              fill='#ffc658'
              isAnimationActive={false}
              stroke='#ffc658'
              type='natural'/>
        <Brush dataKey='index' />
      </LineChart>
    </ResponsiveContainer>
  );
};

FitnessLineChart.propTypes = {
  className: PropTypes.string,
  data: PropTypes.array.isRequired
};

export default FitnessLineChart;
