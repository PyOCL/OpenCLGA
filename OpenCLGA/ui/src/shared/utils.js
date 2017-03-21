export const createSimpleAction = (type) => {
  return (data) => ({ type, data });
};

