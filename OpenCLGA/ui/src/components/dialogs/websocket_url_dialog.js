import React, { Component } from 'react';
import {
  Button,
  FormControl,
  Modal
} from 'react-bootstrap';

class WebSocketURLDialog extends Component {

  constructor(props) {
    super(props);
    this.state = { value: '' };

    this.handleSubmit = ::this.handleSubmit;
    this.handleTextChanged = ::this.handleTextChanged;
  }

  handleTextChanged(e) {
    this.setState({ value: e.target.value });
  }

  handleSubmit() {
    this.props.onClose && this.props.onClose(this.state.value);
  }

  render() {
    return (
      <div>
        <Modal show={true} backdrop={false}>
          <Modal.Header>
            <Modal.Title>WebSocket URL</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <div>Please type WebSocket URL here:</div>
            <FormControl placeholder='ws://your-url[:port]'
                         type='text'
                         value={this.state.value}
                         onChange={this.handleTextChanged} />
            <div>(starting with ws:// or wss://)</div>
          </Modal.Body>
          <Modal.Footer>
            <Button onClick={this.handleSubmit}>Ok</Button>
          </Modal.Footer>
        </Modal>
      </div>
    );
  }

}

export default WebSocketURLDialog;
