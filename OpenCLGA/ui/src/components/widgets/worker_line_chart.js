import React, { Component, PropTypes } from 'react';
import { DropdownButton, MenuItem, Well } from 'react-bootstrap';
import _ from 'lodash';
import LineChart from './line_chart';

class WorkerLineChart extends Component {

  static propTypes = {
    className: PropTypes.string,
    workers: PropTypes.object.isRequired
  };

  constructor(props) {
    super(props);

    const idArray = _.keys(this.props.workers);
    const selected = idArray.length ? idArray[0] : null;

    this.state = { selected};
    this.handleSelected = ::this.handleSelected;
  }

  componentWillReceiveProps(nextProps) {
    if (!_.size(this.props.workers) && _.size(nextProps.workers)) {
      // from no workers to some workers.
      this.setState({
        selected: _.keys(nextProps.workers)[0]
      });
    } else if (_.size(this.props.workers) && !_.size(nextProps.workers)) {
      // from some workers to no workers.
      this.setState({
        selected: null
      });
    } else if (this.state.selected && !nextProps.workers[this.state.selected]) {
      // selected worker is disconnected.
      this.setState({
        selected: _.keys(nextProps.workers)[0]
      });
    }
  }

  mapWorkersToMenuItems(workers) {
    return _.map(workers, (item) => (
      <MenuItem eventKey={item.id} key={item.id}>
        {this.getWorkerInfo(item)}
      </MenuItem>
    ));
  }

  getWorkerInfo(item) {
    return item ? `${item.device}/${item.platform} (${item.ip})` : '(no worker connected)';
  }

  handleSelected(selected) {
    this.setState({ selected });
  }

  render() {
    const activeWorker = this.props.workers[this.state.selected];
    const activeWorkerResult = activeWorker ? _.map(activeWorker.statistics, (item, index) => ({
      ...item,
      index: index + 1
    })) : [];
    return (
      <Well>
        Worker Results:<br/>
        <DropdownButton bsStyle='default' title={this.getWorkerInfo(activeWorker)}
                      className={this.props.className} id='repopulating-type'
                      onSelect={this.handleSelected}>
          {this.mapWorkersToMenuItems(this.props.workers)}
        </DropdownButton>
        {activeWorker && <LineChart data={activeWorkerResult}/> }
      </Well>
    );
  }
}

export default WorkerLineChart;
