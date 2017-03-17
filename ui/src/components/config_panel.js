import React, { Component } from 'react';
import {
  Col,
  Panel,
  Row
} from 'react-bootstrap';
import GenerationsRow from './config/generations_row';
import PopulationsRow from './config/populations_row';
import CrossoverRow from './config/crossover_row';
import MutationRow from './config/mutation_row';
import RepopulationRow from './config/repopulation_row';
import ShareResultRow from './config/share_result_row';

class ConfigPanel extends Component {

  render() {
    const {
      repopulateConfig
    } = this.props.config;

    const actions = this.props.actions;

    return (
      <Panel header='Configuration Panel' bsStyle='success'>
        <Row>
          <Col xs={12} sm={12} md={6}>
            <GenerationsRow />
            <PopulationsRow />
          </Col>
          <Col xs={12} sm={12} md={6}>
            <CrossoverRow />
            <MutationRow />
          </Col>
        </Row>
        <hr/>
        <Row>
          <Col xs={12} sm={12} md={12}>
            <RepopulationRow type={repopulateConfig.type}
                             onSelect={actions.setRepopulateConfigType} />
          </Col>
          <Col xs={12} sm={12} md={12}>
            <ShareResultRow/>
          </Col>
        </Row>
      </Panel>
    );
  }
}

export default ConfigPanel;
