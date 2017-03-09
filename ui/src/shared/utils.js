export const createSimpleAction = (type) => {
  return (item) => ({ type, item });
};

