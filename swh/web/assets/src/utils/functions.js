// utility functions

export function handleFetchError(response) {
  if (!response.ok) {
    throw Error(response.statusText);
  }
  return response;
}

export function handleFetchErrors(responses) {
  for (let i = 0; i < responses.length; ++i) {
    if (!responses[i].ok) {
      throw Error(responses[i].statusText);
    }
  }
  return responses;
}

export function staticAsset(asset) {
  return `${__STATIC__}${asset}`;
}
