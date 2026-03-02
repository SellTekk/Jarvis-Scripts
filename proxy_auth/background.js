var config = {
    mode: 'fixed_servers',
    rules: {
        singleProxy: {
            scheme: 'http',
            host: '185.135.11.34',
            port: parseInt('6021')
        },
        bypassList: ['localhost']
    }
};
chrome.proxy.settings.set({value: config, scope: 'regular'}, function() {});
function callback(details) {
    return {
        authCredentials: {
            username: '5tv0e',
            password: '13gir4m8'
        }
    };
}
chrome.webRequest.onAuthRequired.addListener(
    callback,
    {urls: ["<all_urls>"]},
    ["blocking"]
);