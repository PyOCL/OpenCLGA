import _ from 'lodash';
import { ACTION_KEYS } from '../../src/shared/socket';
import socketReducer, { initialState } from '../../src/reducers/socket.js';

describe('socket', () => {

  let initState;

  const createWorkerCreationAction = (id, device, ip, platform, type) => ({
    type: ACTION_KEYS.WORKER_CONNECTED,
    data: {
      'worker': id,
      'device': device,
      'ip': ip,
      'platform': platform,
      'type': type,
    }
  });
  const createResultAction = (id, best, avg, worst, best_result) => ({
    type: ACTION_KEYS.GENERATION_RESULT,
    data: {
      'worker': id,
      'result': {
        'best_fitness': best,
        'avg_fitness': avg,
        'worst_fitness': worst,
        'best_result': best_result
      }
    }
  });


  beforeEach(() => {
    initState = _.cloneDeep(initialState);
  });

  test('handles worker connected correctly', () => {
    const action = createWorkerCreationAction('123', 'i7 CPU', '127.0.0.1', 'INTEL', 'cpu');
    const actually = socketReducer(initState, action);

    const expected = {
      workers: {
        '123': {
          best: null,
          device: 'i7 CPU',
          ip: '127.0.0.1',
          platform: 'INTEL',
          state: 'waiting',
          statistics: [],
          type: 'cpu',
          id: '123'
        }
      }
    };

    expect(actually).toEqual(expected);
  });

  test('handles generation result correctly', () => {
    const workerAction = createWorkerCreationAction('123', 'i7 CPU', '127.0.0.1', 'INTEL', 'cpu');
    const withWorkerState = socketReducer(initState, workerAction);
    const resultAction = createResultAction('123', 1000, 1234, 2234, ['a']);
    const actually = socketReducer(withWorkerState, resultAction);

    const expected = {
      workers: {
        '123': {
          best: 1000,
          device: 'i7 CPU',
          ip: '127.0.0.1',
          platform: 'INTEL',
          state: 'waiting',
          statistics: [{
            best_fitness: 1000,
            avg_fitness: 1234,
            worst_fitness: 2234,
            best_result: ['a']
          }],
          type: 'cpu',
          id: '123'
        }
      }
    };

    expect(actually).toEqual(expected);
  });
});
