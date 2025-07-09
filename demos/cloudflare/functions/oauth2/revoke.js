// revoke.js - Proxy POST requests to the IdP OAuth2 revoke endpoint.

const IDP_PROTO = 'https';
const IDP_HOST = 'dash.cloudflare.com';
const IDP_PORT = 443;
const IDP_REVOKE_PATH = '/oauth2/revoke';

export async function onRequest(ctx) {
    const url = new URL(ctx.request.url);
    const pathname = url.pathname.replace(/[/]+$/, '');

    // Check if the path is revoke
    if (pathname !== IDP_REVOKE_PATH) {
        const payload = {
            error: 'invalid_request',
            error_verbose: `only ${IDP_REVOKE_PATH} can be proxied`,
            status_code: 400,
        };

        return new Response(JSON.stringify(payload), {
            status: payload.status_code,
            headers: {'Content-Type': 'application/json'}
        });
    }

    if (ctx.request.method !== 'POST') {
        const payload = {
            error: 'invalid_request',
            error_verbose: 'only the POST method is allowed on this endpoint',
            status_code: 400,
        };

        return new Response(JSON.stringify(payload), {
            status: payload.status_code,
            headers: {'Content-Type': 'application/json'}
        });
    }

    console.log(`proxying ${ctx.request.method} request: ${ctx.request.url}`);

    url.protocol = IDP_PROTO + ':';
    url.host = IDP_HOST;
    url.port = IDP_PORT.toString();

    const headers = new Headers([...ctx.request.headers].filter(([header, _]) => !header.match(/^CF-/i)));
    headers.set('Host', url.host);

    console.log(`upstream ${ctx.request.method} request: ${url.toString()}`);
    return await fetch(url, {method: ctx.request.method, headers: headers, body: ctx.request.body});
}

// EOF - revoke.js