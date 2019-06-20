import axios from 'axios';

export async function httpGetJson(url) {
  const response = await axios.get(url);
  return response.data;
}
