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
      actions,
      config
    } = this.props;
    return (
      <Panel header='Configuration Panel' bsStyle='success'>
        <Row>
          <Col xs={12} sm={12} md={6}>
            <GenerationsRow config={config.termination}
                            onChange={actions.setTermination} />
            <PopulationsRow value={config.population}
                            onChange={actions.setPopulation} />
          </Col>
          <Col xs={12} sm={12} md={6}>
            <CrossoverRow value={config.crossoverRatio}
                         onChange={actions.setCrossoverRatio} />
            <MutationRow value={config.mutationRatio}
                          onChange={actions.setMutationRatio} />
          </Col>
        </Row>
        <hr/>
        <Row>
          <Col xs={12} sm={12} md={12}>
            <RepopulationRow config={config.repopulateConfig}
                             onTypeChange={actions.setRepopulateConfigType}
                             onInputChange={actions.setRepopulateConfigDiff} />
          </Col>
          <Col xs={12} sm={12} md={12}>
            <ShareResultRow value={config.shareBestCount}
                            onChange={actions.setShareBestCount} />
          </Col>
        </Row>
      </Panel>
    );
  }
}

export default ConfigPanel;
