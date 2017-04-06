import React, { Component } from 'react';
import {
  Col,
  ControlLabel,
  Radio,
  Row
} from 'react-bootstrap';
import NumericInput from 'react-numeric-input';

const DEFAULTS = {
  count: 1000,
  time: 10
}

class GenerationRow extends Component {

  constructor(props) {
    super(props);
    this.state = {
      count: DEFAULTS.count,
      time: DEFAULTS.time
    }
    this.handleRadioChanged = this.handleRadioChanged.bind(this);
    this.handleValueChange = this.handleValueChange.bind(this);
  }

  handleRadioChanged(evt) {
    const type = evt.target.value;
    const value = this.state[type];
    this.props.onChange(type, value);
  }

  handleValueChange(value) {
    const type = this.props.config.type || 'count';
    this.setState({
      [type]: value
    }, () => {
      this.props.onChange(type, value);
    });
  }

  render() {
    const {
      config,
      disabled
    } = this.props;

    const countChecked = config.type === 'count';
    const timeChecked = config.type === 'time';
    return (
      <Row className='generations-row'>
        <Col xs={12} sm={4} md={4}><ControlLabel>Generations:</ControlLabel></Col>
        <Col xs={12} sm={8} md={8}>
          <div>
            <Radio checked={countChecked} disabled={disabled} name='generationType' value='count'
                   onChange={this.handleRadioChanged}>
              By count:
            </Radio>
            <NumericInput className='generations-count-number'
                          min={1} value={this.state.count} max={1000000000} step={1000}
                          onChange={this.handleValueChange} disabled={!countChecked || disabled} />
          </div>
          <div>
            <Radio checked={timeChecked} disabled={disabled} name='generationType' value='time'
                   onChange={this.handleRadioChanged}>
              By time (mins):
            </Radio>
            <NumericInput className='generations-time-number'
                          min={1} value={this.state.time} max={1000000000} step={1}
                          onChange={this.handleValueChange} disabled={!timeChecked || disabled} />
          </div>
        </Col>
      </Row>
    );
  }
}

export default GenerationRow;
