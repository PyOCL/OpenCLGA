import React, { PropTypes } from 'react';
import { Well } from 'react-bootstrap';
import {
  BootstrapTable,
  TableHeaderColumn,
} from 'react-bootstrap-table';
import _ from 'lodash';
import { formatFitness, formatGeneration } from '../../shared/utils';


const COLUMN_MAPPING = [
  {
    header: 'ID',
    dataField: 'id',
    iskey: true
  }, {
    header: 'IP',
    dataField: 'ip',
  }, {
    header: 'Device',
    dataField: 'device',
  }, {
    header: 'platform',
    dataField: 'platform'
  }, {
    header: 'Type',
    dataField: 'type'
  }, {
    header: 'Generations',
    dataField: 'generationCount',
    dataFormat: (cell, row) => formatGeneration(cell)
  }, {
    header: 'Best Fitness',
    dataField: 'best',
    dataFormat: (cell, row) => _.isNil(cell) ? 'N/A' : formatFitness(cell)
  }
];

const renderColumns = (props) => {
  return COLUMN_MAPPING.map((item) => (
    <TableHeaderColumn dataField={item.dataField}
                       dataFormat={item.dataFormat}
                       dataSort={true}
                       isKey={item.iskey}
                       key={item.dataField}>
      {item.header}
    </TableHeaderColumn>
  ));
}

const ClientsTable = (props) => {

  return (
    <Well>
      <BootstrapTable className={props.className}
                      data={props.clients}>
        {renderColumns(props)}
      </BootstrapTable>
    </Well>
  );
};

ClientsTable.propTypes = {
  className: PropTypes.string,
  clients: PropTypes.array.isRequired
};

export default ClientsTable;
