import React, { Component } from 'react';
import {
  ButtonToolbar,
  Col,
  Panel,
  Row
} from 'react-bootstrap';
import GenerationsRow from './config/generations_row';
import PopulationsRow from './config/populations_row';
import CrossoverRow from './config/crossover_row';
import MutationRow from './config/mutation_row';
import RepopulateTypeDropdown from './repopulate_type_dropdown';

class ConfigPanel extends Component {

  render() {
    const {
      repopulateConfig
    } = this.props.config;

    const actions = this.props.actions;

    return (
      <Panel header='Configuration Panel' bsStyle='success'>
        <Row>
          <Col xs={12} sm={12} md={7}>
            <GenerationsRow />
            <PopulationsRow />
          </Col>
          <Col xs={12} sm={12} md={5}>
            <CrossoverRow />
            <MutationRow />
          </Col>
        </Row>
        <Row>
          <hr/>
          <ButtonToolbar>
            <RepopulateTypeDropdown value={repopulateConfig.type}
                                    onSelect={actions.setRepopulateConfigType} />
          </ButtonToolbar>
        </Row>
      </Panel>
    );
  }
}

export default ConfigPanel;
