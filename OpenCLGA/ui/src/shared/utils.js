import numeral from 'numeral';

export const createSimpleAction = (type) => (data) => ({ type, data });
export const formatFitness = (value) => numeral(value).format('0,0.0000');
export const formatGeneration = (value) => numeral(value).format('0,0');
