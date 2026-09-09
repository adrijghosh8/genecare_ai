import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize } from "node:path";

const root = process.cwd();

const types = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg"
};

const server = createServer(async (request, response) => {
    try {
        const url = new URL(
            request.url,
            `http://${request.headers.host}`
        );

        let requestedPath = url.pathname;

        // Homepage
        if (requestedPath === "/") {
            requestedPath = "/pages/index.html";
        }

        // HTML pages are stored inside /pages
        else if (requestedPath.endsWith(".html")) {
            requestedPath = `/pages${requestedPath}`;
        }

        // robots.txt and favicon are stored inside /public
        else if (
            requestedPath === "/robots.txt" ||
            requestedPath === "/favicon.ico"
        ) {
            requestedPath = `/public${requestedPath}`;
        }

        const file = normalize(join(root, requestedPath));

        // Prevent accessing files outside the frontend directory
        if (!file.startsWith(root)) {
            response.writeHead(403, {
                "Content-Type": "text/plain; charset=utf-8"
            });
            response.end("Forbidden");
            return;
        }

        const content = await readFile(file);

        response.writeHead(200, {
            "Content-Type":
                types[extname(file)] ||
                "application/octet-stream"
        });

        response.end(content);

    } catch (error) {
        if (response.headersSent) {
            response.end();
            return;
        }

        response.writeHead(404, {
            "Content-Type": "text/plain; charset=utf-8"
        });

        response.end("File not found");
    }
});

const PORT = process.env.PORT || 5173;

server.listen(PORT, () => {
    console.log(`GeneCare frontend: http://localhost:${PORT}`);
});