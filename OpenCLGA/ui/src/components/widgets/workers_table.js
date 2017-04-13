import React, { Component, PropTypes } from 'react';
import { Well } from 'react-bootstrap';
import {
  Column,
  Table
} from 'fixed-data-table';
import Measure from 'react-measure';
import _ from 'lodash';
import { formatFitness, formatGeneration } from '../../shared/utils';

const ROW_HEIGHT = 36;

const COLUMN_MAPPING = [
  {
    header: 'ID',
    dataField: 'id',
    width: 80
  }, {
    header: 'IP',
    dataField: 'ip',
    width: 90
  }, {
    header: 'Device',
    dataField: 'device',
    width: 240
  }, {
    header: 'platform',
    dataField: 'platform',
    width: 110
  }, {
    header: 'Type',
    dataField: 'type',
    width: 60,
  }, {
    header: 'Generations',
    dataField: 'generationCount',
    dataFormat: (cell, row) => formatGeneration(cell),
    width: 89
  }, {
    header: 'Best Fitness',
    dataField: 'best',
    dataFormat: (cell, row) => _.isNil(cell) ? 'N/A' : formatFitness(cell),
    width: 110
  }
];

const TextCell = ({rowIndex, data, col, ...props}) => {
  const text = col.dataFormat ? col.dataFormat(data[rowIndex][col.dataField])
                              : data[rowIndex][col.dataField];
  const lineHeightStyle = { lineHeight: ROW_HEIGHT + 'px' };
  return (<div title={text}
               className='grid-text-cell'
               style={lineHeightStyle}>
            {text}
          </div>);
};

class WorkersTable extends Component {

  constructor(props) {
    super(props);
    const columnSize = _.reduce(COLUMN_MAPPING, (acc, item, key) => {
      acc[item.dataField] = item.width;
      return acc;
    }, {});
    this.state = { columnSize };
  }

  handleColumnResized(size, key) {
    this.setState({
      columnSize: {
        ...this.state.columnSize,
        [key]: size
      }
    });
  }

  renderColumns() {
    const { columnSize } = this.state;
    return COLUMN_MAPPING.map((item) => (
      <Column header={item.header}
              cell={<TextCell data={this.props.workers} col={item}/>}
              width={columnSize[item.dataField]}
              isResizable={true}
              columnKey={item.dataField}
              flexGrow={1}
              key={item.dataField}/>
    ));
  }

  render() {
    // The div wrapping a Table is important for auto-resizing. I don't know why
    // but it works.
    return (
      <Well>
        <Measure>
          { dimensions =>
            <div>
              <Table className={this.props.className}
                     isColumnResizing={false}
                     rowsCount={this.props.workers.length}
                     onColumnResizeEndCallback={::this.handleColumnResized}
                     width={dimensions.width}
                     rowHeight={ROW_HEIGHT}
                     headerHeight={ROW_HEIGHT}
                     height={200}
                     data={this.props.workers}
                     {...this.props}>
                {this.renderColumns()}
              </Table>
            </div>
          }
        </Measure>
      </Well>
    );
  }
}

WorkersTable.propTypes = {
  className: PropTypes.string,
  workers: PropTypes.array.isRequired
};

export default WorkersTable;
