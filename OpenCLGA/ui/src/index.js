import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux'
import { createStore, applyMiddleware, compose } from 'redux';
import thunk from 'redux-thunk';

import Main from './main';
import rootReducer from './reducers/index';
import socket from './actions/socket';
import './styles/index.css';

(function init() {
  let store;


  const initStore = () => {
    const composeEnhancers = window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ || compose;

    return new Promise((resolve, reject) => {
      store = createStore(
        rootReducer,
        composeEnhancers(applyMiddleware(thunk))
      );
      resolve(store);
    });
  };

  const initUI = (store) => {
    ReactDOM.render(
      <Provider store={store}>
        <Main />
      </Provider>,
      document.getElementById('root')
    );
  };

  initStore().then((store) => {
    socket.init(store);
    initUI(store);
  });
})();
