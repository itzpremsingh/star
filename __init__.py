import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable, Dict, List, Union

from .converters import converters
from .utils import render


class Request:
    """Stores query parameters of the current request."""

    args: Dict[str, Any] = {}


class Star:
    """Main Star framework class."""

    def __init__(self) -> None:
        self.get_routes: Dict[str, Callable[..., Any]] = {}
        self.post_routes: Dict[str, Callable[..., Any]] = {}

    def route(
        self, url: str, method: Union[str, List[str]] = "GET"
    ) -> Callable[..., Callable[..., Any]]:
        """
        Register a route with the given URL and HTTP method(s).
        Example: @star.route("/hello", "GET")
        """
        if not isinstance(method, list):
            method = [method]

        def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
            for m in method:
                m_upper = m.upper()
                if m_upper == "GET":
                    self.get_routes[url.rstrip("/")] = func
                elif m_upper == "POST":
                    self.post_routes[url.rstrip("/")] = func
                else:
                    raise ValueError(f"Invalid method: {m}")
            return func

        return wrapper

    def get(self, url: str) -> Callable[..., Callable[..., Any]]:
        """Shortcut decorator for GET requests."""
        return self.route(url, "GET")

    def post(self, url: str) -> Callable[..., Callable[..., Any]]:
        """Shortcut decorator for POST requests."""
        return self.route(url, "POST")

    def run(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Run the HTTP server."""

        outer_self = self  # Capture Star instance for inner Handler

        class Handler(BaseHTTPRequestHandler):
            """Handles incoming HTTP requests."""

            def do_GET(self) -> None:
                outer_self._handle_request(self, outer_self.get_routes)

            def do_POST(self) -> None:
                outer_self._handle_request(self, outer_self.post_routes)

        server = HTTPServer((host, port), Handler)
        print(f"Server running at http://{host}:{port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.server_close()
            print("Server stopped")

    def _handle_request(
        self, handler: BaseHTTPRequestHandler, routes: Dict[str, Callable[..., Any]]
    ) -> None:
        """Internal request handling with exact and dynamic route matching."""
        path: str = handler.path.split("?")[0].rstrip("/")
        Request.args = self._parse_args(handler.path)
        matched: bool = False
        params: List[Any] = []

        for url, func in routes.items():
            normalized_url: str = url.rstrip("/")

            # Exact match
            if path == normalized_url:
                matched = True

            # Dynamic route with type converters
            if path != "/" and not matched:
                regex_pattern = re.sub(
                    r"<(int|string|float):(\w+)>", self._replace, normalized_url
                )
                match = re.fullmatch(regex_pattern, path)
                if match:
                    convs = re.findall(r"<(int|string|float):\w+>", normalized_url)
                    params = [
                        converters[conv].convert(value)
                        for conv, value in zip([c[0] for c in convs], match.groups())
                    ]
                    matched = True

            # Dynamic route without type
            if path != "/" and not matched:
                regex_pattern = re.sub(
                    r"<(\w+)>", f"(?P<var>{converters['string'].regex})", normalized_url
                )
                match = re.fullmatch(regex_pattern, path)
                if match:
                    params = list(match.groups())
                    matched = True

            # Query string match
            if not matched and Request.args and path == normalized_url:
                matched = True

            if matched:
                self._send_response(handler, func, params)
                return

        # 404 Not Found
        handler.send_response(404)
        handler.send_header("Content-type", "text/html")
        handler.end_headers()
        handler.wfile.write(
            render(
                "star/templates/error.html",
                {"title": "404 Not Found", "message": "Page Not Found"},
            ).encode()
        )

    def _send_response(
        self,
        handler: BaseHTTPRequestHandler,
        func: Callable[..., Any],
        params: List[Any],
    ) -> None:
        """Send the HTTP response to the client."""
        handler.send_response(200)
        handler.send_header("Content-type", "text/html")
        handler.end_headers()
        try:
            result = func(*params)
        except Exception as e:
            result = render(
                "star/templates/error.html",
                {"title": "500 Internal Server Error", "message": str(e)},
            )
        handler.wfile.write(result.encode())

    def _parse_args(self, path: str) -> Dict[str, str]:
        """Parse query parameters from URL into Request.args."""
        if "?" not in path:
            return {}
        query_string: str = path.split("?")[1]
        args: Dict[str, str] = {}
        for part in query_string.split("&"):
            if "=" in part:
                key, value = part.split("=")
                args[key] = value
        return args

    def _replace(self, match: re.Match[str]) -> str:
        """Convert typed URL patterns to regex groups."""
        conv, var = match.groups()
        return f"(?P<{var}>{converters[conv].regex})"
