const csrfSettings = document.body.dataset;
const config = JSON.parse(document.getElementById("swagger-settings").textContent);

config.dom_id = "#swagger-ui";
config.presets = [
    SwaggerUIBundle.presets.apis,
    SwaggerUIBundle.SwaggerUIStandalonePreset,
];

if (csrfSettings.apiCsrf) {
    config.requestInterceptor = (request) => {
        // Django rotates the CSRF cookie after login; read it for every request.
        const cookie = document.cookie.split("; ").find((part) => part.startsWith("csrftoken="));
        const token = cookie ? decodeURIComponent(cookie.substring("csrftoken=".length)) : csrfSettings.csrfToken;
        if (token) {
            request.headers["X-CSRFToken"] = token;
        }
        return request;
    };
}

SwaggerUIBundle(config);
