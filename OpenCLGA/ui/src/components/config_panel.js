import React, { Component } from 'react';
import {
  Col,
  Panel,
  Row
} from 'react-bootstrap';
import { OPENCLGA_STATES } from '../shared/constants';
import GenerationRow from './config/generation_row';
import PopulationRow from './config/population_row';
import CrossoverRow from './config/crossover_row';
import MutationRow from './config/mutation_row';
import ExtinctionRow from './config/extinction_row';
import ElitismModeRow from './config/elitism_mode_row';

class ConfigPanel extends Component {

  render() {
    const {
      actions,
      state,
      config
    } = this.props;
    const isWaiting = state === OPENCLGA_STATES.WAITING;
    const isPaused = state === OPENCLGA_STATES.PAUSED;
    const isPrepared = state === OPENCLGA_STATES.PREPARED;
    return (
      <Panel header='Configuration Panel' bsStyle='success'>
        <Row>
          <Col xs={12} sm={12} md={6}>
            <GenerationRow disabled={!isWaiting}
                           config={config.termination}
                           onChange={actions.setTermination} />
            <PopulationRow disabled={!isWaiting}
                           value={config.population}
                           onChange={actions.setPopulation} />
          </Col>
          <Col xs={12} sm={12} md={6}>
            <CrossoverRow disabled={!isWaiting && !isPaused && !isPrepared}
                          value={config.crossoverRatio}
                          onChange={actions.setCrossoverRatio} />
            <MutationRow disabled={!isWaiting && !isPaused && !isPrepared}
                         value={config.mutationRatio}
                         onChange={actions.setMutationRatio} />
          </Col>
        </Row>
        <hr/>
        <Row>
          <Col xs={12} sm={12} md={12}>
            <ExtinctionRow disabled={!isWaiting}
                           config={config.extinctionConfig}
                           onTypeChange={actions.setExtinctionConfigType}
                           onInputChange={actions.setExtinctionConfigDiff} />
          </Col>
          <Col xs={12} sm={12} md={12}>
            <ElitismModeRow disabled={!isWaiting}
                            value={config.elitismMode}
                            onChange={actions.setElitismMode} />
          </Col>
        </Row>
      </Panel>
    );
  }
}

export default ConfigPanel;
