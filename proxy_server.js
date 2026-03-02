const ProxyChain = require('proxy-chain');

const server = new ProxyChain.Server({
  port: 9999,
  prepareRequestFunction: ({ request, username, password, hostname, port, isHttp, connectionId }) => {
    return {
      requestAuthentication: false,
      upstreamProxyUrl: 'http://5tv0e:13gir4m8@185.135.11.34:6021',
    };
  },
});

server.listen(() => {
  console.log(`Proxy server is listening on port ${server.port}`);
});

server.on('requestFailed', ({ request, error }) => {
  console.log(`Request ${request.url} failed`);
  console.error(error);
});